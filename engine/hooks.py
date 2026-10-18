"""Claude Code hook handlers.

Each takes the hook's JSON payload and the plugin data dir, and returns what to print on
stdout for Claude Code (or None).
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from engine.detect import run_detectors
from engine.ledger import Ledger
from engine.models import SnitchEvent

SESSION_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")


class HookError(ValueError):
    pass


def session_dir(data_dir: Path, session_id: object) -> Path:
    # session_id becomes a directory name: plain ids only, never a path
    if not isinstance(session_id, str) or not SESSION_ID.fullmatch(session_id):
        raise HookError(f"invalid session_id: {session_id!r}")
    return data_dir / "sessions" / session_id


def toplevel(cwd: Path) -> Path | None:
    """Root of the git work tree containing `cwd`, or None outside one."""
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(top.stdout.strip()).resolve() if top.returncode == 0 else None


def _listed(root: Path) -> list[str]:
    """Tracked and untracked, non-ignored files of the git work tree at `root`."""
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout.decode()
    return [
        rel
        for rel in dict.fromkeys(filter(None, out.split("\0")))
        # tracked but deleted in the work tree
        if (root / rel).is_file() or (root / rel).is_symlink()
    ]


def snapshot(root: Path, dest: Path, files: list[str] | None = None) -> None:
    # shortcut: copies every file each time; switch to hardlinks or content
    # hashes if large repos make hooks slow.
    for rel in _listed(root) if files is None else files:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, target, follow_symlinks=False)


def _fingerprint(root: Path, files: list[str]) -> str:
    """Changes whenever a file is added, removed, resized or rewritten."""
    digest = hashlib.sha1()
    for rel in files:
        stat = (root / rel).lstat()
        digest.update(f"{rel}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode())
    return digest.hexdigest()


def session_start(payload: dict[str, Any], data_dir: Path) -> None:
    """Snapshot the baseline once per session."""
    session = session_dir(data_dir, payload.get("session_id"))
    root = toplevel(Path(str(payload.get("cwd") or ".")))
    if root is not None:
        session.mkdir(parents=True, exist_ok=True)
        # rewritten on resume too: its mtime marks the project's active session
        (session / "project").write_text(str(root))
    baseline = session / "baseline"
    if baseline.exists():
        return  # resume / compact: the first baseline stays
    if root is None:
        # stderr, not stdout: SessionStart stdout becomes Claude's context
        print(
            f"snitch: {payload.get('cwd')} is not a git repository; no baseline taken",
            file=sys.stderr,
        )
        return
    partial = session / "baseline.partial"
    shutil.rmtree(partial, ignore_errors=True)
    snapshot(root, partial)
    # rename last, so a crash mid-copy never leaves a half baseline behind
    partial.rename(baseline)


def current_session(data_dir: Path, project: Path) -> str | None:
    """The most recently started session on the repo at `project` (its git root).

    MCP servers get no session id, only the project dir.
    """
    # shortcut: two Claude sessions open on the same project share the newest one;
    # revisit if Claude Code starts passing the session id to MCP servers.
    root = toplevel(project)
    if root is None:
        return None
    marks = [
        p
        for p in (data_dir / "sessions").glob("*/project")
        if p.read_text() == str(root)
    ]
    newest = max(marks, key=lambda p: p.stat().st_mtime_ns, default=None)
    return newest.parent.name if newest else None


def _feedback(events: list[SnitchEvent]) -> str:
    lines = [f"Snitch flagged {len(events)} new test-integrity event(s):"]
    for e in events:
        where = f"{e.file}:{e.line_start}"
        if e.line_end != e.line_start:
            where += f"-{e.line_end}"
        lines.append(f"- [{e.severity}] {e.pattern} at {where}")
    lines.append(
        "If a test is wrong, do not weaken, skip or delete it: call the snitch "
        "`escalate` tool with the test id and your reason instead. If this change was "
        "intended, disclose it in your final message."
    )
    return "\n".join(lines)


def post_tool(payload: dict[str, Any], data_dir: Path) -> str | None:
    """Detect against the baseline; in warn/enforce mode, tell the agent about new events."""
    session_id = payload.get("session_id")
    session = session_dir(data_dir, session_id)
    assert isinstance(session_id, str)  # validated by session_dir
    baseline = session / "baseline"
    root = toplevel(Path(str(payload.get("cwd") or ".")))
    project = session / "project"
    if not baseline.is_dir() or root is None or not project.is_file():
        return None
    if project.read_text() != str(root):
        return (
            None  # cwd moved to another repo: its tree says nothing about this baseline
        )
    files = _listed(root)
    fingerprint = _fingerprint(root, files)
    state = session / "fingerprint"
    if state.is_file() and state.read_text() == fingerprint:
        return None  # nothing changed since the last run (most Bash calls)

    with tempfile.TemporaryDirectory() as tmp:
        current = Path(tmp) / "current"
        snapshot(root, current, files)
        events, warnings = run_detectors(baseline, current, session_id)
    for warning in warnings:
        print(f"snitch: {warning}", file=sys.stderr)

    ledger = Ledger(data_dir / "ledger.db")
    try:
        known = {e.id for e in ledger.events(session_id)}
        ledger.record(events)
        stored = ledger.events(session_id)  # with `escalated` filled in
    finally:
        ledger.close()
    state.write_text(fingerprint)

    new = [e for e in stored if e.id not in known and not e.escalated]
    mode = os.environ.get("CLAUDE_PLUGIN_OPTION_MODE", "warn")
    if not new or mode == "observe":
        return None
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": _feedback(new),
            }
        }
    )
