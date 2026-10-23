"""snitch-mcp: gives the agent an honest alternative to changing a test it thinks is wrong."""

import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from engine.hooks import current_session, recorded_data_dir, toplevel
from engine.ledger import Ledger
from engine.receipt import render

server = MCPServer(
    "snitch",
    instructions=(
        "Snitch watches this session for test tampering. If a test looks wrong, "
        "call `escalate` instead of editing, skipping or weakening it."
    ),
)


def _project() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def _session() -> tuple[Path, str | None]:
    value = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if value and "${" not in value:
        data: Path | None = Path(value)
    else:
        data = recorded_data_dir(_project())
    if data is None:
        return Path(value or "<CLAUDE_PLUGIN_DATA unset>"), None
    return data, current_session(data, _project())


def _repo_relative(test_id: str) -> str:
    """`test_id` with its file part relative to the repo root, as events store it."""
    file, sep, name = test_id.partition("::")
    project = _project()
    root = toplevel(project)
    if root is not None:
        path = (project / file).resolve()
        if not path.exists():
            path = (root / file).resolve()  # pytest node ids are rootdir-relative
        try:
            file = path.relative_to(root).as_posix()
        except ValueError:
            pass  # outside the repo: keep it as given
    return file + sep + name


@server.tool()
def escalate(test_id: str, reason: str, evidence: str = "") -> str:
    """Report a test you believe is wrong, instead of changing it.

    Use this when a test contradicts the spec or the user's request, is flaky, or
    cannot pass for reasons outside the code under test. Do not edit, skip or weaken
    the test afterwards; explain the problem in your final message.

    Args:
        test_id: pytest node id (`tests/test_x.py::test_name`) or the test file path.
        reason: why the test is wrong.
        evidence: where that shows (spec line, issue, command output), if any.
    """
    data, session_id = _session()
    if session_id is None:
        return (
            f"no Snitch session found for {_project()} in {data}, so nothing was "
            "recorded. "
            "Still leave the test unchanged and explain the problem to the user."
        )
    ledger = Ledger(data / "ledger.db")
    try:
        ledger.escalate(session_id, _repo_relative(test_id), reason, evidence)
    finally:
        ledger.close()
    return (
        f"Escalation recorded for {test_id}. Leave the test unchanged and explain the "
        "problem in your final message."
    )


@server.tool()
def ledger() -> str:
    """The integrity receipt for this session: every test-integrity event so far."""
    data, session_id = _session()
    if session_id is None or not (data / "ledger.db").exists():
        return render([])
    store = Ledger(data / "ledger.db")
    try:
        return render(store.events(session_id))
    finally:
        store.close()
