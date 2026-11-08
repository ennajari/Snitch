"""Hollow tests (spec): mutate the source lines a change touched and run only the tests
the change added. If most mutants survive, those tests check little of what changed.

Slow (one pytest run per mutant), so it never runs in a hook: `snitch mutate` only.
"""

import ast
import difflib
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from engine.astdiff.diff import (
    PARSER,
    _is_test_file,
    _py_files,
    _tests,
    python_file_patterns,
)
from engine.models import SnitchEvent, new_event

MAX_MUTANTS = 12
MIN_MUTANTS = 3
# shortcut: a handful of classic operators; widen when hollow tests slip through
SWAPS: dict[type, type] = {
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Lt: ast.GtE,
    ast.GtE: ast.Lt,
    ast.Gt: ast.LtE,
    ast.LtE: ast.Gt,
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.FloorDiv,
    ast.And: ast.Or,
    ast.Or: ast.And,
}


def _changed_lines(before: Path | None, after: Path) -> set[int]:
    old = before.read_text().splitlines() if before else []
    new = after.read_text().splitlines()
    lines: set[int] = set()
    for tag, _, _, j1, j2 in difflib.SequenceMatcher(a=old, b=new).get_opcodes():
        if tag in ("replace", "insert"):
            lines.update(range(j1 + 1, j2 + 1))
    return lines


def _mutants(source: str, lines: set[int]) -> Iterator[tuple[int, str]]:
    """(line, mutated module source), one mutation per mutant, on `lines` only."""
    tree = ast.parse(source)
    spots = [n for n in ast.walk(tree) if getattr(n, "lineno", None) in lines]
    for node in spots:
        for field in ("op", "ops", "value"):
            original = getattr(node, field, None)
            if field == "ops" and isinstance(original, list):
                swapped = [SWAPS.get(type(o), type(o))() for o in original]
                if [type(o) for o in swapped] == [type(o) for o in original]:
                    continue
                setattr(node, field, swapped)
            elif field == "op" and type(original) in SWAPS:
                setattr(node, field, SWAPS[type(original)]())
            elif field == "value" and isinstance(node, ast.Constant):
                if isinstance(original, bool):
                    node.value = not original
                elif isinstance(original, int | float):
                    node.value = original + 1
                else:
                    continue
            elif (
                field == "value"
                and isinstance(node, ast.Return)
                and original is not None
            ):
                node.value = ast.Constant(None)
            else:
                continue
            yield getattr(node, "lineno", 0), ast.unparse(tree)
            setattr(node, field, original)


def _new_tests(
    before_repo: Path, after_repo: Path, patterns: tuple[str, ...]
) -> list[str]:
    before_files, after_files = _py_files(before_repo), _py_files(after_repo)
    found = []
    for rel, path in after_files.items():
        if not _is_test_file(path, patterns):
            continue
        old = set()
        if rel in before_files:
            old = {
                n
                for n, _ in _tests(
                    PARSER.parse(before_files[rel].read_bytes()).root_node, rel
                )
            }
        tree = PARSER.parse(path.read_bytes())
        found += [n for n, _ in _tests(tree.root_node, rel) if n not in old]
    return found


def _passes(repo: Path, tests: list[str], python: str) -> bool:
    try:
        done = subprocess.run(
            [
                python,
                "-m",
                "pytest",
                "-x",
                "-q",
                "-p",
                "no:cacheprovider",
                "-o",
                "addopts=",
                *tests,
            ],
            cwd=repo,
            capture_output=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False  # a mutant that hangs counts as caught
    return done.returncode == 0


def diff_mutation(
    before_repo: Path,
    after_repo: Path,
    *,
    session_id: str = "local",
    python: str | None = None,
) -> list[SnitchEvent]:
    """One `hollow_tests` event when the tests a change added (passing unmutated)
    still pass against at least half of the mutants of the source lines it changed."""
    python = python or sys.executable
    patterns = python_file_patterns(before_repo, after_repo)
    tests = _new_tests(before_repo, after_repo, patterns)
    if not tests:
        return []
    before_files = _py_files(before_repo)
    sources = {
        rel: _changed_lines(before_files.get(rel), path)
        for rel, path in _py_files(after_repo).items()
        if not _is_test_file(path, patterns) and path.name != "conftest.py"
    }
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(shutil.copytree(after_repo, Path(tmp) / "work"))
        if not _passes(work, tests, python):
            return []  # failing tests are not hollow; other detectors cover them
        tried = survived = 0
        for rel, lines in sources.items():
            if not lines:
                continue
            target = work / rel
            original = target.read_text()
            for _, mutated in _mutants(original, lines):
                if tried == MAX_MUTANTS:
                    break
                target.write_text(mutated)
                tried += 1
                survived += _passes(work, tests, python)
            target.write_text(original)
    # shortcut: a fixed bar; calibrate it on real agent-written tests
    if tried < MIN_MUTANTS or survived * 2 < tried:
        return []
    first = tests[0].split("::", 1)[0]
    return [
        new_event(
            session_id=session_id,
            family="hollow",
            pattern="hollow_tests",
            severity="medium",
            nodeid=first,
            file=first,
            line_start=1,
            line_end=1,
            before=None,
            after=f"{len(tests)} new test(s) passed against {survived} of {tried} mutants of the changed code: "
            + ", ".join(tests),
            detector="mutation",
            created_at=datetime.now(UTC),
        )
    ]
