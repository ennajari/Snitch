"""Claude Code hook handlers.

Each takes the hook's JSON payload and the plugin data dir, and returns what to print on
stdout for Claude Code (or None).
"""

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from engine.astdiff.diff import _is_test_file, enclosing_test, python_file_patterns
from engine.detect import run_detectors
from engine.ledger import Ledger
from engine.models import SnitchEvent
from engine.policy import POLICY
from engine.rules.diff import TEST_RUNNER

SESSION_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
# session baselines are full copies of the repo: drop them after two idle weeks
RETENTION_SECONDS = 14 * 24 * 3600


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


def _data_pointer(root: Path) -> Path:
    """`<git dir>/snitch/plugin-data`: the plugin data dir, for the MCP server."""
    git_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return Path(git_dir) / "snitch" / "plugin-data"


def recorded_data_dir(project: Path) -> Path | None:
    """The plugin data dir the last SessionStart on this repo used, if any."""
    # MCP servers should get ${CLAUDE_PLUGIN_DATA} expanded, but `claude plugin eval`
    # passes it through literally; SessionStart leaves this pointer for that case.
    root = toplevel(project)
    pointer = _data_pointer(root) if root is not None else None
    return Path(pointer.read_text()) if pointer and pointer.is_file() else None


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


def _drop_stale_sessions(data_dir: Path, keep: Path) -> None:
    sessions = data_dir / "sessions"
    if not sessions.is_dir():
        return
    cutoff = time.time() - RETENTION_SECONDS
    for session in sessions.iterdir():
        mark = session / "project"  # rewritten whenever the session starts or resumes
        last_used = (mark if mark.is_file() else session).stat().st_mtime
        if session != keep and last_used < cutoff:
            shutil.rmtree(session, ignore_errors=True)


def session_start(payload: dict[str, Any], data_dir: Path) -> str | None:
    """Snapshot the baseline once per session, and drop stale sessions' data. In
    warn/enforce mode, give the agent the anti-reward-hacking policy."""
    session = session_dir(data_dir, payload.get("session_id"))
    _drop_stale_sessions(data_dir, keep=session)
    root = toplevel(Path(str(payload.get("cwd") or ".")))
    if root is not None:
        session.mkdir(parents=True, exist_ok=True)
        # rewritten on resume too: its mtime marks the project's active session
        (session / "project").write_text(str(root))
        pointer = _data_pointer(root)
        pointer.parent.mkdir(exist_ok=True)
        pointer.write_text(str(data_dir.resolve()))
    if root is None:
        # stderr, not stdout: SessionStart stdout becomes Claude's context
        print(
            f"snitch: {payload.get('cwd')} is not a git repository; no baseline taken",
            file=sys.stderr,
        )
        return None
    baseline = session / "baseline"
    if not baseline.exists():  # resume / compact: the first baseline stays
        partial = session / "baseline.partial"
        shutil.rmtree(partial, ignore_errors=True)
        snapshot(root, partial)
        # rename last, so a crash mid-copy never leaves a half baseline behind
        partial.rename(baseline)
    if _mode() == "observe":
        return None  # observe never changes what the agent does
    # also on resume / compact: compaction can drop the earlier context
    context = {"hookEventName": "SessionStart", "additionalContext": POLICY}
    return json.dumps({"hookSpecificOutput": context})


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


def _listing(events: list[SnitchEvent]) -> list[str]:
    lines = []
    for e in events:
        where = f"{e.file}:{e.line_start}"
        if e.line_end != e.line_start:
            where += f"-{e.line_end}"
        lines.append(f"- [{e.severity}] {e.pattern} at {where}")
    return lines


def _session_events(
    payload: dict[str, Any], data_dir: Path
) -> tuple[str, list[SnitchEvent], set[str]] | None:
    """Detect if the tree changed since the last run, then return (session id, the
    session's stored events, ids stored before this call). None without a baseline."""
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

    ledger = Ledger(data_dir / "ledger.db")
    try:
        known = {e.id for e in ledger.events(session_id)}
        # unchanged since the last run (most Bash calls): skip the detectors
        if not (state.is_file() and state.read_text() == fingerprint):
            with tempfile.TemporaryDirectory() as tmp:
                current = Path(tmp) / "current"
                snapshot(root, current, files)
                events, warnings = run_detectors(
                    baseline,
                    current,
                    session_id,
                    # the baseline never changes within a session: collect it once
                    before_cache=session / "baseline-inventory.json",
                )
                found = {
                    e.id: enclosing_test(current / e.file, e.line_start) for e in events
                }
            for warning in warnings:
                print(f"snitch: {warning}", file=sys.stderr)
            ledger.record(events, {k: v for k, v in found.items() if v})
            state.write_text(fingerprint)
        return session_id, ledger.events(session_id), known
    finally:
        ledger.close()


MODES = ("observe", "warn", "enforce")


def _mode() -> str:
    """The userConfig `mode`; the /config picker limits it, settings.json may not."""
    mode = os.environ.get("CLAUDE_PLUGIN_OPTION_MODE", "").strip().lower() or "warn"
    if mode not in MODES:
        print(f"snitch: unknown mode {mode!r}, using warn", file=sys.stderr)
        return "warn"
    return mode


def post_tool(payload: dict[str, Any], data_dir: Path) -> str | None:
    """Detect against the baseline; in warn/enforce mode, tell the agent about new events."""
    found = _session_events(payload, data_dir)
    if found is None:
        return None
    _, stored, known = found
    new = [e for e in stored if e.id not in known and not e.escalated]
    if not new or _mode() == "observe":
        return None
    lines = [f"Snitch flagged {len(new)} new test-integrity event(s):", *_listing(new)]
    lines.append(
        "If a test is wrong, do not weaken, skip or delete it: call the snitch "
        "`escalate` tool with the test id and your reason instead. If this change was "
        "intended, disclose it in your final message."
    )
    context = {"hookEventName": "PostToolUse", "additionalContext": "\n".join(lines)}
    return json.dumps({"hookSpecificOutput": context})


def _mentions(message: str, file: str, test: str | None = None) -> bool:
    # shortcut: "disclosed" = the final message names the file (repo path or file
    # name) or the changed test; the LLM judge (later phase) decides whether it really
    # owns up to the change.
    text = message.lower()
    if file.lower() in text or Path(file).name.lower() in text:
        return True
    return (
        bool(test)
        and re.search(rf"\b{re.escape(str(test).lower())}\b", text) is not None
    )


EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
PASS_CLAIM = re.compile(
    r"\b(tests?|test suite|suite)\b[^.\n]{0,40}?\b(pass(es|ed|ing)?|green)\b"
    r"|\b\d+ passed\b",
    re.IGNORECASE,
)
NEGATION = re.compile(r"\b(not|never|no|fail\w*)\b|n't", re.IGNORECASE)


def _claims_untested_pass(transcript: object, message: str) -> bool:
    """The final message says the tests pass, yet no test command ran after the
    agent's last file edit (spec: "claimed to run tests but never did")."""
    claims = [m.group(0) for m in PASS_CLAIM.finditer(message)]
    if not transcript or not any(not NEGATION.search(c) for c in claims):
        return False
    try:
        lines = Path(str(transcript)).read_text().splitlines()
    except OSError:
        return False  # no transcript: nothing to check against
    edited = tested = False
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        body = entry.get("message") if isinstance(entry, dict) else None
        content = body.get("content") if isinstance(body, dict) else None
        for part in content if isinstance(content, list) else []:
            if not isinstance(part, dict) or part.get("type") != "tool_use":
                continue
            # shortcut: only edit tools count as edits, not files written via Bash
            if part.get("name") in EDIT_TOOLS:
                edited, tested = True, False
            elif part.get("name") == "Bash":
                command = str((part.get("input") or {}).get("command", ""))
                tested = tested or bool(TEST_RUNNER.search(command))
    return edited and not tested


def stop(payload: dict[str, Any], data_dir: Path) -> str | None:
    """Undisclosed, unescalated events at the end of a turn, or a "tests pass" claim
    with no test run since the last edit: warn the user, or (enforce) block the stop
    once and ask the agent to revert, disclose, escalate or run the tests."""
    found = _session_events(payload, data_dir)
    if found is None:
        return None
    _, stored, _ = found
    message = str(payload.get("last_assistant_message") or "")
    unresolved = [e for e in stored if not e.escalated and e.disclosed is not True]
    root = toplevel(Path(str(payload.get("cwd") or ".")))
    flags = {
        e.id: _mentions(
            message,
            e.file,
            enclosing_test(root / e.file, e.line_start) if root else None,
        )
        for e in unresolved
    }
    if flags:
        ledger = Ledger(data_dir / "ledger.db")
        try:
            ledger.set_disclosed(flags)
        finally:
            ledger.close()
    hidden = [e for e in unresolved if not flags[e.id]]
    untested = _claims_untested_pass(payload.get("transcript_path"), message)
    if not (hidden or untested) or _mode() == "observe":
        return None
    listing = "\n".join(_listing(hidden))
    # stop_hook_active: Claude is already continuing because of a stop hook, so
    # blocking again could loop forever; fall back to telling the user.
    if _mode() == "enforce" and not payload.get("stop_hook_active"):
        reasons = []
        if hidden:
            reasons.append(
                "Snitch: your final message does not disclose these test changes:\n"
                f"{listing}\n"
                "Before finishing, either revert them, or say plainly which test file "
                "you changed and why. If a test is wrong, call the snitch `escalate` tool."
            )
        if untested:
            reasons.append(
                "Snitch: your final message says the tests pass, but no test command "
                "ran after your last edit. Run the tests, or correct your message."
            )
        return json.dumps({"decision": "block", "reason": "\n\n".join(reasons)})
    notes = []
    if hidden:
        notes.append(
            "Snitch: the agent did not disclose these test changes:\n"
            f"{listing}\nAsk Claude for the snitch ledger to see the full receipt."
        )
    if untested:
        notes.append(
            "Snitch: the agent says the tests pass, but no test command ran after "
            "its last edit."
        )
    return json.dumps({"systemMessage": "\n\n".join(notes)})


def _frozen(root: Path) -> list[str]:
    """Glob patterns (repo-relative) that the agent may not edit, from .snitch.toml."""
    path = root / ".snitch.toml"
    if not path.is_file():
        return []
    try:
        frozen = tomllib.loads(path.read_text()).get("frozen", [])
    except tomllib.TOMLDecodeError as exc:
        raise HookError(f"{path}: {exc}") from None
    if not isinstance(frozen, list) or not all(isinstance(g, str) for g in frozen):
        raise HookError(f"{path}: `frozen` must be a list of glob strings")
    return frozen


def _repo_path(root: Path, path: Path) -> str | None:
    """`path` relative to the repo root, or None outside the repo."""
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return None


def _is_frozen(rel: str | None, frozen: list[str]) -> bool:
    # shortcut: fnmatch's `*` also crosses `/` ("tests/*" covers subfolders);
    # switch to PurePath.full_match once we require Python 3.13.
    return rel is not None and any(fnmatch(rel, glob) for glob in frozen)


def _segments(command: str) -> list[list[str]]:
    """Words of each simple command in a shell line (split on ; && || | & and parens)."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:  # unbalanced quotes
        tokens = command.split()
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token and all(c in "();<>|&" for c in token):
            segments.append([])
        else:
            segments[-1].append(token)
    return [words for words in segments if words]


def _in_place(word: str) -> bool:
    if word.startswith("--"):
        return word == "--in-place" or word.startswith("--in-place=")
    return word.startswith("-") and "i" in word[1:]  # -i, -i.bak, -Ei


# perl's -i, alone or in a cluster of argument-less switches (-pi, -i.bak, -pie)
PERL_IN_PLACE = re.compile(r"-[aclnpsTtuUwW]*i")


def _bash_problem(command: str, cwd: Path, root: Path, frozen: list[str]) -> str | None:
    # shortcut: catches sed -i, perl -i and git --no-verify only; `cd` inside the line,
    # redirections and python one-liners still get through to the PostToolUse detectors.
    for words in _segments(command):
        program = Path(words[0]).name
        if program == "git" and "--no-verify" in words:
            return "`--no-verify` skips the repository's git hooks"
        in_place = _in_place if program == "sed" else PERL_IN_PLACE.match
        if program not in ("sed", "perl") or not any(in_place(w) for w in words[1:]):
            continue
        for word in words[1:]:
            target = Path(word)
            is_test = target.suffix == ".py" and _is_test_file(
                target, python_file_patterns(root)
            )
            if not word.startswith("-") and (
                is_test or _is_frozen(_repo_path(root, cwd / target), frozen)
            ):
                return f"`{program} -i` would rewrite {word} in place"
    return None


def pre_tool(payload: dict[str, Any], data_dir: Path) -> str | None:
    """Enforce mode: deny edits to frozen paths, `sed -i` on tests and `--no-verify`."""
    if _mode() != "enforce":
        return None
    cwd = Path(str(payload.get("cwd") or "."))
    root = toplevel(cwd)
    tool_input = payload.get("tool_input")
    if root is None or not isinstance(tool_input, dict):
        return None
    frozen = _frozen(root)
    if payload.get("tool_name") == "Bash":
        problem = _bash_problem(str(tool_input.get("command") or ""), cwd, root, frozen)
    else:  # Edit, Write, MultiEdit
        file_path = tool_input.get("file_path")
        rel = _repo_path(root, cwd / str(file_path)) if file_path else None
        problem = (
            f"{rel} is frozen in .snitch.toml" if _is_frozen(rel, frozen) else None
        )
    if problem is None:
        return None
    reason = (
        f"Snitch (enforce mode) blocked this: {problem}. If a test or check looks "
        "wrong, do not change or bypass it: call the snitch `escalate` tool with the "
        "test id, your reason and evidence, then carry on with the rest of the task."
    )
    decision = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
    return json.dumps({"hookSpecificOutput": decision})
