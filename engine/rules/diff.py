import configparser
import re
import shlex
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from tree_sitter import Node

from engine.astdiff.diff import PARSER, _is_test_file, _py_files, _text, _walk
from engine.models import SnitchEvent, new_event

# shortcut: config files are read at the repo root only; walk the tree when a
# monorepo with per-package pytest/coverage config needs it.
CONFIGS = ("pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg", ".coveragerc")
REPORT_HOOKS = {
    "pytest_runtest_makereport",
    "pytest_runtest_logreport",
    "pytest_report_teststatus",
}
DESELECTING = {
    "-k",
    "-m",
    "--deselect",
    "--ignore",
    "--ignore-glob",
    "--collect-only",
    "--co",
}
BROAD = {"Exception", "BaseException"}
# shortcut: CI files are matched line by line, not parsed as YAML; add a YAML
# parser (new dependency) if multi-line scalars or anchors hide these.
CI_RULES = (
    ("ci_continue_on_error", re.compile(r"continue-on-error:\s*true")),
    ("ci_or_true", re.compile(r"\|\|\s*true\b")),
    ("ci_no_verify", re.compile(r"--no-verify")),
)
SPECIAL_CASING = re.compile(
    r"""PYTEST_CURRENT_TEST|["']pytest["']\s+in\s+sys\.modules"""
)

type Family = Literal["tampering", "evasion", "faking", "hollow"]


def _read(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(errors="replace")


def _added(before: Path | None, after: Path) -> list[tuple[int, str]]:
    """(line number, stripped text) of non-comment lines that the before file lacks."""
    old = {line.strip() for line in _read(before).splitlines()}
    return [
        (number, text)
        for number, line in enumerate(_read(after).splitlines(), 1)
        if (text := line.strip()) and text not in old and not text.startswith("#")
    ]


def _line_of(path: Path, pattern: str) -> int:
    for number, line in enumerate(_read(path).splitlines(), 1):
        if re.search(pattern, line):
            return number
    return 1


def _tokens(addopts: str | None) -> list[str]:
    if not addopts:
        return []
    try:
        return shlex.split(addopts)
    except ValueError:  # unbalanced quotes
        return addopts.split()


def _config(path: Path) -> tuple[str | None, float | None]:
    """(addopts, coverage threshold) of one config file; (None, None) if unreadable."""
    addopts: object = None
    fail_under: object = None
    if path.name == "pyproject.toml":
        try:
            tool = tomllib.loads(_read(path)).get("tool", {})
            addopts = tool.get("pytest", {}).get("ini_options", {}).get("addopts")
            fail_under = tool.get("coverage", {}).get("report", {}).get("fail_under")
        except (tomllib.TOMLDecodeError, AttributeError):
            return None, None
        if isinstance(addopts, list):
            addopts = shlex.join(map(str, addopts))
    else:
        ini = configparser.ConfigParser(interpolation=None)
        try:
            ini.read_string(_read(path))
        except configparser.Error:
            return None, None
        for section in ("pytest", "tool:pytest"):
            addopts = addopts or ini.get(section, "addopts", fallback=None)
        for section in ("report", "coverage:report"):
            fail_under = fail_under or ini.get(section, "fail_under", fallback=None)
    opts = " ".join(addopts.split()) if isinstance(addopts, str) else None

    candidates = [fail_under]
    tokens = _tokens(opts)
    for i, token in enumerate(tokens):
        if token.startswith("--cov-fail-under="):
            candidates.append(token.split("=", 1)[1])
        elif token == "--cov-fail-under" and i + 1 < len(tokens):
            candidates.append(tokens[i + 1])
    for candidate in candidates:
        try:
            return opts, float(str(candidate))
        except ValueError:
            continue
    return opts, None


def _deselects(token: str) -> bool:
    return token.split("=", 1)[0] in DESELECTING or token.startswith(("no:", "-pno:"))


def _report_hooks(root: Node) -> dict[str, Node]:
    """Hook name -> its definition (decorators included)."""
    hooks = {}
    for node in _walk(root):
        name = node.child_by_field_name("name")
        if node.type == "function_definition" and name is not None:
            parent = node.parent
            decorated = parent is not None and parent.type == "decorated_definition"
            if _text(name) in REPORT_HOOKS:
                hooks[_text(name)] = parent if parent and decorated else node
    return hooks


def _broad_excepts(root: Node) -> list[Node]:
    """`except:` / `except Exception:` clauses whose body is only `pass`."""
    found = []
    for node in _walk(root):
        if node.type != "except_clause":
            continue
        value = node.child_by_field_name("value")
        caught = _text(value).split(" as ")[0].strip() if value else None
        body = [
            stmt
            for block in node.named_children
            if block.type == "block"
            for stmt in block.named_children
            if stmt.type != "comment"
        ]
        if (
            (caught is None or caught in BROAD)
            and body
            and all(stmt.type == "pass_statement" for stmt in body)
        ):
            found.append(node)
    return found


def diff_rules(
    before_repo: Path, after_repo: Path, *, session_id: str = "local"
) -> list[SnitchEvent]:
    now = datetime.now(UTC)
    events: list[SnitchEvent] = []

    def emit(
        family: Family,
        pattern: str,
        file: str,
        line_start: int,
        line_end: int,
        before: str | None,
        after: str | None,
        severity: Literal["medium", "high"] = "high",
    ) -> None:
        events.append(
            new_event(
                session_id=session_id,
                family=family,
                pattern=pattern,
                severity=severity,
                # no test node here: one event per (pattern, file)
                nodeid=file,
                file=file,
                line_start=line_start,
                line_end=line_end,
                before=before,
                after=after,
                detector="rule",
                created_at=now,
            )
        )

    def emit_lines(
        family: Family, pattern: str, file: str, hits: list[tuple[int, str]]
    ) -> None:
        if hits:
            emit(
                family,
                pattern,
                file,
                hits[0][0],
                hits[-1][0],
                None,
                "\n".join(text for _, text in hits),
            )

    before_py = _py_files(before_repo)
    after_py = _py_files(after_repo)

    for file, path in after_py.items():
        if path.name != "conftest.py":
            continue
        # Trees must outlive their nodes.
        old_tree = PARSER.parse(_read(before_py.get(file)).encode())
        tree = PARSER.parse(_read(path).encode())
        old_hooks = _report_hooks(old_tree.root_node)
        hooks = {
            name: node
            for name, node in _report_hooks(tree.root_node).items()
            if name not in old_hooks
        }
        if hooks:
            emit(
                "tampering",
                "conftest_report_hook",
                file,
                min(n.start_point.row for n in hooks.values()) + 1,
                max(n.end_point.row for n in hooks.values()) + 1,
                None,
                ", ".join(hooks),
            )

    for name in CONFIGS:
        path = after_repo / name
        if not path.is_file():
            continue
        old_opts, old_threshold = _config(before_repo / name)
        opts, threshold = _config(path)
        old_tokens = _tokens(old_opts)
        if any(_deselects(t) for t in _tokens(opts) if t not in old_tokens):
            line = _line_of(path, r"^\s*addopts\s*=")
            emit(
                "evasion", "addopts_changed", name, line, line, old_opts, opts, "medium"
            )
        if old_threshold is not None and (
            threshold is None or threshold < old_threshold
        ):
            line = _line_of(path, r"fail_under|cov-fail-under")
            emit(
                "tampering",
                "coverage_threshold_lowered",
                name,
                line,
                line,
                f"{old_threshold:g}",
                None if threshold is None else f"{threshold:g}",
            )

    ci_files = sorted(after_repo.glob(".github/workflows/*.y*ml"))
    ci_files.append(after_repo / ".gitlab-ci.yml")
    for path in ci_files:
        if not path.is_file():
            continue
        file = path.relative_to(after_repo).as_posix()
        added = _added(before_repo / file, path)
        for pattern, regex in CI_RULES:
            emit_lines(
                "evasion", pattern, file, [h for h in added if regex.search(h[1])]
            )

    for file, path in after_py.items():
        if _is_test_file(path) or path.name == "conftest.py":
            continue
        old_path = before_py.get(file)
        emit_lines(
            "faking",
            "test_env_special_casing",
            file,
            [h for h in _added(old_path, path) if SPECIAL_CASING.search(h[1])],
        )

        old_tree = PARSER.parse(_read(old_path).encode())
        tree = PARSER.parse(_read(path).encode())
        old_tries = {
            _text(n) for n in _walk(old_tree.root_node) if n.type == "try_statement"
        }
        swallowed = [
            clause
            for clause in _broad_excepts(tree.root_node)
            if clause.parent is not None and _text(clause.parent) not in old_tries
        ]
        if swallowed:
            emit(
                "hollow",
                "broad_except_pass",
                file,
                swallowed[0].start_point.row + 1,
                swallowed[-1].end_point.row + 1,
                None,
                "\n".join(map(_text, swallowed)),
                "medium",
            )
    return events
