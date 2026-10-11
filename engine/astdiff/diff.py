import textwrap
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import tree_sitter_python
from tree_sitter import Language, Node, Parser

from engine.models import SnitchEvent, new_event

PARSER = Parser(Language(tree_sitter_python.language()))
LITERALS = {"integer", "float", "string", "true", "false", "none"}
SKIP_CALLS = {"pytest.skip", "pytest.xfail", "skip", "xfail"}
APPROX_CALLS = {"pytest.approx", "approx"}
# pytest.approx defaults, used when the `before` side gives no explicit tolerance
APPROX_DEFAULTS = {"rel": 1e-6, "abs": 1e-12}


def _text(node: Node) -> str:
    """Source of `node`, with the continuation lines of a block dedented."""
    raw = (node.text or b"").decode()
    return textwrap.dedent(" " * node.start_point.column + raw)


def _walk(node: Node) -> Iterator[Node]:
    yield node
    for child in node.children:
        yield from _walk(child)


def _is_test_file(path: Path) -> bool:
    # shortcut: pytest's default naming only; read python_files / python_functions
    # from the repo's config when a project with custom patterns needs it.
    return path.name.startswith("test_") or path.name.endswith("_test.py")


def _py_files(repo: Path) -> dict[str, Path]:
    return {
        p.relative_to(repo).as_posix(): p
        for p in sorted(repo.rglob("*.py"))
        if not any(part.startswith(".") for part in p.relative_to(repo).parts)
    }


def _tests(root: Node, prefix: str) -> Iterator[tuple[str, Node]]:
    """(node id without parametrize suffix, function node) for each test in a file."""
    for child in root.named_children:
        node = child
        if node.type == "decorated_definition":
            node = node.child_by_field_name("definition") or node
        name = node.child_by_field_name("name")
        body = node.child_by_field_name("body")
        if name is None or body is None:
            continue
        label = _text(name)
        if node.type == "function_definition" and label.startswith("test"):
            yield f"{prefix}::{label}", child
        elif node.type == "class_definition" and label.startswith("Test"):
            yield from _tests(body, f"{prefix}::{label}")


def _asserts(fn: Node) -> list[Node]:
    return [n for n in _walk(fn) if n.type == "assert_statement"]


def _skip_calls(fn: Node) -> list[Node]:
    return [
        n
        for n in _walk(fn)
        if n.type == "call"
        and (callee := n.child_by_field_name("function")) is not None
        and _text(callee) in SKIP_CALLS
    ]


def _guard(node: Node, fn: Node) -> Node | None:
    """Outermost `if` / `try ... except` around `node` that can keep it from running."""
    guard = None
    parent = node.parent
    while parent is not None and parent != fn:
        if parent.type == "if_statement" or (
            parent.type == "try_statement"
            and any(c.type.startswith("except") for c in parent.children)
        ):
            guard = parent
        parent = parent.parent
    return guard


def _equality(assertion: Node) -> list[Node] | None:
    """The two operands of `assert a == b`, else None."""
    cond = assertion.named_children[0]
    if cond.type != "comparison_operator":
        return None
    operators = [o.type for o in cond.children_by_field_name("operators")]
    return cond.named_children if operators == ["=="] else None


def _tolerance(assertion: Node) -> dict[str, float] | None:
    """Explicit rel= / abs= of the first pytest.approx call; None if there is no call."""
    for node in _walk(assertion):
        callee = node.child_by_field_name("function")
        args = node.child_by_field_name("arguments")
        if node.type != "call" or callee is None or args is None:
            continue
        if _text(callee) not in APPROX_CALLS:
            continue
        found = {}
        for arg in args.named_children:
            name = arg.child_by_field_name("name")
            value = arg.child_by_field_name("value")
            if arg.type == "keyword_argument" and name and value:
                try:
                    found[_text(name)] = float(_text(value))
                except ValueError:
                    pass  # not a numeric literal: cannot compare
        return found
    return None


def _weakened(before: Node, after: Node) -> bool:
    operands = _equality(before)
    if operands is None:
        return False
    cond = after.named_children[0]
    # truthy-only: `assert x == 5` became `assert x`
    if _text(cond) in {_text(o) for o in operands}:
        return True
    if cond.type == "comparison_operator":
        operators = [o.type for o in cond.children_by_field_name("operators")]
        if operators == ["in"]:
            return True
        if operators == ["is not"] and cond.named_children[-1].type == "none":
            return True
    old, new = _tolerance(before), _tolerance(after)
    if old is None or new is None:
        return False
    return any(
        new[key] > old.get(key, default)
        for key, default in APPROX_DEFAULTS.items()
        if key in new
    )


def _is_literal(node: Node) -> bool:
    if node.type == "unary_operator":
        node = node.child_by_field_name("argument") or node
    return node.type in LITERALS


def _literal_changed(before: Node, after: Node) -> bool:
    old, new = _equality(before), _equality(after)
    if old is None or new is None:
        return False
    return any(
        _is_literal(o) and _is_literal(n) and _text(o) != _text(n)
        for o, n in zip(old, new, strict=False)
    )


def _pair(
    before: list[Node], after: list[Node]
) -> tuple[list[tuple[Node, Node]], list[tuple[Node, Node]], list[Node]]:
    """Split asserts into (unchanged pairs, changed pairs, removed)."""
    by_text: dict[str, list[Node]] = {}
    for node in after:
        by_text.setdefault(_text(node), []).append(node)
    same, rest_before = [], []
    for node in before:
        twins = by_text.get(_text(node))
        if twins:
            same.append((node, twins.pop(0)))
        else:
            rest_before.append(node)
    rest_after = sorted(
        (n for nodes in by_text.values() for n in nodes), key=lambda n: n.start_byte
    )
    changed = list(zip(rest_before, rest_after, strict=False))
    return same, changed, rest_before[len(rest_after) :]


def diff_ast(
    before_repo: Path, after_repo: Path, *, session_id: str = "local"
) -> list[SnitchEvent]:
    before_files = _py_files(before_repo)
    after_files = _py_files(after_repo)
    now = datetime.now(UTC)

    def sources(files: dict[str, Path]) -> dict[str, bytes]:
        return {f: p.read_bytes() for f, p in files.items() if not _is_test_file(p)}

    # shortcut: repo-wide, any non-test .py counts as "the code under test";
    # resolve the test file's imports if unrelated edits make this noisy.
    source_changed = sources(before_files) != sources(after_files)

    events: list[SnitchEvent] = []
    for file, after_path in after_files.items():
        before_path = before_files.get(file)
        if before_path is None or not _is_test_file(after_path):
            continue
        # Trees must outlive their nodes.
        before_tree = PARSER.parse(before_path.read_bytes())
        after_tree = PARSER.parse(after_path.read_bytes())
        before_tests = dict(_tests(before_tree.root_node, file))
        after_tests = dict(_tests(after_tree.root_node, file))
        # Asserts of tests that are new in this file: a "removed" assert found here
        # was moved by a test split, not dropped.
        moved = {
            _text(a)
            for nodeid, fn in after_tests.items()
            if nodeid not in before_tests
            for a in _asserts(fn)
        }

        for nodeid, fn in after_tests.items():
            old_fn = before_tests.get(nodeid)
            if old_fn is None:
                continue

            def emit(
                pattern: str,
                befores: list[Node],
                afters: list[Node],
                *,
                family: Literal["tampering", "evasion"] = "tampering",
                severity: Literal["medium", "high"] = "high",
                # bound now: the closure is called within this iteration only
                nodeid: str = nodeid,
                file: str = file,
                fn: Node = fn,
            ) -> None:
                span = afters or [fn]
                events.append(
                    new_event(
                        session_id=session_id,
                        family=family,
                        pattern=pattern,
                        severity=severity,
                        nodeid=nodeid,
                        file=file,
                        line_start=min(n.start_point.row for n in span) + 1,
                        line_end=max(n.end_point.row for n in span) + 1,
                        before="\n".join(map(_text, befores)) or None,
                        after="\n".join(map(_text, afters)) or None,
                        detector="ast",
                        created_at=now,
                    )
                )

            same, changed, removed = _pair(_asserts(old_fn), _asserts(fn))
            removed = [a for a in removed if _text(a) not in moved]
            if removed:
                emit("assertion_removed", removed, [])

            weakened = [(b, a) for b, a in changed if _weakened(b, a)]
            if weakened:
                emit(
                    "assertion_weakened",
                    [b for b, _ in weakened],
                    [a for _, a in weakened],
                )

            relit = [
                (b, a)
                for b, a in changed
                if (b, a) not in weakened and _literal_changed(b, a)
            ]
            if relit and source_changed:
                emit(
                    "expected_value_changed",
                    [b for b, _ in relit],
                    [a for _, a in relit],
                    severity="medium",
                )

            old_skips, skips = _skip_calls(old_fn), _skip_calls(fn)
            if len(skips) > len(old_skips):
                emit("skip_in_body", [], skips[len(old_skips) :], family="evasion")

            guarded = [
                (b, guard)
                for b, a in same + changed
                if _guard(b, old_fn) is None and (guard := _guard(a, fn)) is not None
            ]
            if guarded:
                emit(
                    "assertion_guarded",
                    [b for b, _ in guarded],
                    # two asserts under one guard report that guard once
                    list({g.start_byte: g for _, g in guarded}.values()),
                )
    return events
