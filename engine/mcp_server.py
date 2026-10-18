"""snitch-mcp: gives the agent an honest alternative to changing a test it thinks is wrong."""

import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from engine.hooks import current_session
from engine.ledger import Ledger
from engine.receipt import render

server = MCPServer(
    "snitch",
    instructions=(
        "Snitch watches this session for test tampering. If a test looks wrong, "
        "call `escalate` instead of editing, skipping or weakening it."
    ),
)


def _session() -> tuple[Path, str | None]:
    data = Path(os.environ["CLAUDE_PLUGIN_DATA"])
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    return data, current_session(data, project)


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
            "no Snitch session found for this project, so nothing was recorded. "
            "Still leave the test unchanged and explain the problem to the user."
        )
    ledger = Ledger(data / "ledger.db")
    try:
        ledger.escalate(session_id, test_id, reason, evidence)
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
