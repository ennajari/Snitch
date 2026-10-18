import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

import typer

from engine import hooks
from engine.detect import run_detectors
from engine.ledger import Ledger
from engine.receipt import render

app = typer.Typer(help="Snitch: catches coding agents that cheat on tests.")
hook_app = typer.Typer(help="Claude Code hook handlers (read the hook JSON on stdin).")
app.add_typer(hook_app, name="hook")


@app.callback()
def main() -> None:
    """Snitch: catches coding agents that cheat on tests."""


def _fail(message: str) -> typer.Exit:
    typer.echo(message, err=True)
    return typer.Exit(2)


def _git(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise _fail(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _commit(ref: str) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise _fail(f"not a commit: {ref}")
    return proc.stdout.strip()


def _export_commit(sha: str, dest: Path) -> None:
    proc = subprocess.run(["git", "archive", sha], capture_output=True, check=False)
    if proc.returncode != 0:
        raise _fail(f"git archive {sha} failed: {proc.stderr.decode().strip()}")
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tar:
        tar.extractall(dest, filter="data")


def _run(before: Path, after: Path, session_id: str) -> None:
    """Run every detector, record the events, print the receipt, exit 1 on any event."""
    events, warnings = run_detectors(before, after, session_id)
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)

    # Inside the git dir: never committed, no .gitignore entry needed.
    db = Path(_git("rev-parse", "--path-format=absolute", "--git-common-dir"))
    (db / "snitch").mkdir(exist_ok=True)
    ledger = Ledger(db / "snitch" / "ledger.db")
    try:
        ledger.record(events)
    finally:
        ledger.close()

    typer.echo(render(events), nl=False)
    raise typer.Exit(1 if events else 0)


@app.command()
def diff(
    base: Annotated[str, typer.Argument(help="Commit before the change.")],
    head: Annotated[str, typer.Argument(help="Commit after the change.")],
) -> None:
    """Check the changes between two commits."""
    shas = [_commit(base), _commit(head)]
    with tempfile.TemporaryDirectory() as tmp:
        before, after = Path(tmp) / "before", Path(tmp) / "after"
        _export_commit(shas[0], before)
        _export_commit(shas[1], after)
        _run(before, after, f"diff:{shas[0]}..{shas[1]}")


@app.command()
def check(
    staged: Annotated[
        bool, typer.Option("--staged", help="Check the staged changes against HEAD.")
    ] = False,
) -> None:
    """Check uncommitted changes."""
    if not staged:
        raise _fail("only `snitch check --staged` is supported for now")
    sha = _commit("HEAD")
    root = Path(_git("rev-parse", "--show-toplevel"))
    with tempfile.TemporaryDirectory() as tmp:
        before, after = Path(tmp) / "before", Path(tmp) / "after"
        _export_commit(sha, before)
        _git("-C", str(root), "checkout-index", "-a", f"--prefix={after}/")
        _run(before, after, f"staged:{sha}")


def _hook(handler: Callable[[dict[str, Any], Path], str | None]) -> None:
    """Run a hook handler on the stdin payload; print what it returns for Claude Code."""
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not data:
        typer.echo(
            "snitch: CLAUDE_PLUGIN_DATA is not set; run from the plugin", err=True
        )
        raise typer.Exit(1)
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise hooks.HookError("hook payload is not a JSON object")
        out = handler(payload, Path(data))
    except (json.JSONDecodeError, hooks.HookError) as exc:
        # exit 1: a non-blocking error for every hook event (exit 2 would block some)
        typer.echo(f"snitch: {exc}", err=True)
        raise typer.Exit(1) from None
    if out:
        typer.echo(out)


@hook_app.command("session-start")
def hook_session_start() -> None:
    """SessionStart: snapshot the working tree as this session's baseline."""
    _hook(hooks.session_start)


@hook_app.command("pre-tool")
def hook_pre_tool() -> None:
    """PreToolUse (enforce): deny edits to frozen paths, sed -i on tests, --no-verify."""
    _hook(hooks.pre_tool)


@hook_app.command("post-tool")
def hook_post_tool() -> None:
    """PostToolUse: run the detectors against the baseline, record, tell the agent."""
    _hook(hooks.post_tool)


@hook_app.command("stop")
def hook_stop() -> None:
    """Stop: check that the agent disclosed or escalated every event of the session."""
    _hook(hooks.stop)


@app.command()
def mcp() -> None:
    """Run snitch-mcp (the escalate and ledger tools) over stdio."""
    from engine.mcp_server import server  # the MCP SDK is only needed here

    server.run()
