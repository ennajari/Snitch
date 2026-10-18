import asyncio
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from typer.testing import CliRunner

from engine.cli import app
from engine.ledger import Ledger
from engine.mcp_server import escalate, ledger, server
from engine.models import SnitchEvent, new_event

runner = CliRunner()


def start_session(data: Path, repo: Path, session_id: str) -> None:
    payload = {"session_id": session_id, "cwd": str(repo), "source": "startup"}
    result = runner.invoke(
        app,
        ["hook", "session-start"],
        input=json.dumps(payload),
        env={"CLAUDE_PLUGIN_DATA": str(data)},
    )
    assert result.exit_code == 0, result.output


def git_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    (path / "test_calc.py").write_text("def test_add():\n    assert 1 + 1 == 2\n")
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    return path


@pytest.fixture
def session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """A started session "s1" on a repo; the server env points at both."""
    data, repo = tmp_path / "data", git_repo(tmp_path / "repo")
    start_session(data, repo, "s1")
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(data))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    return data, repo


def event(session_id: str, file: str) -> SnitchEvent:
    return new_event(
        session_id=session_id,
        family="tampering",
        pattern="assertion_weakened",
        nodeid=f"{file}::test_add",
        file=file,
        line_start=2,
        line_end=2,
        before="assert 1 + 1 == 2",
        after="assert 1 + 1",
        detector="ast",
        created_at=datetime.now(UTC),
    )


def test_server_exposes_escalate_and_ledger() -> None:
    names = {t.name for t in asyncio.run(server.list_tools())}

    assert names == {"escalate", "ledger"}


def test_escalate_marks_the_session_events(session: tuple[Path, Path]) -> None:
    data, _ = session
    store = Ledger(data / "ledger.db")
    store.record([event("s1", "test_calc.py")])
    store.close()

    reply = escalate(
        "test_calc.py::test_add", "expects 3, the spec says 2", "spec.md:4"
    )

    assert "recorded" in reply
    store = Ledger(data / "ledger.db")
    assert [e.escalated for e in store.events("s1")] == [True]
    store.close()


def test_tools_use_the_newest_session_of_this_project(
    tmp_path: Path, session: tuple[Path, Path]
) -> None:
    data, repo = session
    other = git_repo(tmp_path / "other")
    start_session(data, repo, "s2")  # newer, same project
    start_session(data, other, "s3")  # newest, other project
    store = Ledger(data / "ledger.db")
    store.record([event("s1", "test_calc.py"), event("s2", "test_calc.py")])
    store.close()

    escalate("test_calc.py", "wrong", "")

    store = Ledger(data / "ledger.db")
    assert [e.escalated for e in store.events("s1")] == [False]
    assert [e.escalated for e in store.events("s2")] == [True]
    store.close()


def test_ledger_tool_returns_the_receipt(session: tuple[Path, Path]) -> None:
    data, _ = session
    store = Ledger(data / "ledger.db")
    store.record([event("s1", "test_calc.py")])
    store.close()

    receipt = ledger()

    assert receipt.startswith("# Snitch receipt")
    assert "assertion_weakened" in receipt


def test_without_a_session_nothing_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path / "data"))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(git_repo(tmp_path / "repo")))

    reply = escalate("test_calc.py", "wrong", "")

    assert "no Snitch session" in reply
    assert not (tmp_path / "data" / "ledger.db").exists()


def test_snitch_mcp_speaks_mcp_over_stdio(session: tuple[Path, Path]) -> None:
    data, repo = session
    params = StdioServerParameters(
        command=str(Path(sys.executable).parent / "snitch"),
        args=["mcp"],
        env={
            **os.environ,
            "CLAUDE_PLUGIN_DATA": str(data),
            "CLAUDE_PROJECT_DIR": str(repo),
        },
    )

    async def talk() -> tuple[set[str], str]:
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as client,
        ):
            await client.initialize()
            tools = {t.name for t in (await client.list_tools()).tools}
            result = await client.call_tool("ledger", {})
            return tools, result.content[0].text  # type: ignore[union-attr]

    tools, receipt = asyncio.run(talk())

    assert tools == {"escalate", "ledger"}
    assert receipt.startswith("# Snitch receipt")


def test_project_dir_may_be_a_subdirectory(
    session: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    data, repo = session
    (repo / "src").mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo / "src"))
    store = Ledger(data / "ledger.db")
    store.record([event("s1", "test_calc.py")])
    store.close()

    reply = escalate("test_calc.py", "wrong", "")

    assert "recorded" in reply
    store = Ledger(data / "ledger.db")
    assert [e.escalated for e in store.events("s1")] == [True]
    store.close()


@pytest.mark.parametrize("form", ["absolute", "./test_calc.py::test_add"])
def test_escalate_accepts_other_path_forms(
    session: tuple[Path, Path], form: str
) -> None:
    data, repo = session
    store = Ledger(data / "ledger.db")
    store.record([event("s1", "test_calc.py")])
    store.close()
    test_id = f"{repo / 'test_calc.py'}::test_add" if form == "absolute" else form

    escalate(test_id, "wrong", "")

    store = Ledger(data / "ledger.db")
    assert [e.escalated for e in store.events("s1")] == [True]
    store.close()
