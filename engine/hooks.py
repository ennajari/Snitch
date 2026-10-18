"""Claude Code hook handlers. Each takes the hook's JSON payload and the plugin data dir."""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

SESSION_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")


class HookError(ValueError):
    pass


def session_dir(data_dir: Path, session_id: object) -> Path:
    # session_id becomes a directory name: plain ids only, never a path
    if not isinstance(session_id, str) or not SESSION_ID.fullmatch(session_id):
        raise HookError(f"invalid session_id: {session_id!r}")
    return data_dir / "sessions" / session_id


def snapshot(root: Path, dest: Path) -> None:
    """Copy tracked and untracked, non-ignored files of the git work tree at `root`."""
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout.decode()
    # shortcut: copies every file on each new session; switch to hardlinks or
    # content hashes if large repos make session start slow.
    for rel in dict.fromkeys(filter(None, listed.split("\0"))):
        src = root / rel
        if not src.is_file() and not src.is_symlink():
            continue  # tracked but deleted in the work tree
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target, follow_symlinks=False)


def session_start(payload: dict[str, Any], data_dir: Path) -> str | None:
    """Snapshot the baseline once per session; returns a note for stderr, if any."""
    session = session_dir(data_dir, payload.get("session_id"))
    baseline = session / "baseline"
    if baseline.exists():
        return None  # resume / compact: the first baseline stays
    cwd = Path(str(payload.get("cwd") or "."))
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if top.returncode != 0:
        return f"snitch: {cwd} is not a git repository; no baseline taken"
    partial = session / "baseline.partial"
    shutil.rmtree(partial, ignore_errors=True)
    snapshot(Path(top.stdout.strip()), partial)
    # rename last, so a crash mid-copy never leaves a half baseline behind
    partial.rename(baseline)
    return None
