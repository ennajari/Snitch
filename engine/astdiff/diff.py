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
SKIP_CALLS = {"pytest.skip", "pytest.xfail", "skip", "xfail", "self.skipTest"}
APPROX_CALLS = {"pytest.approx", "approx"}
UNITTEST_EQUAL = {"self.assertEqual", "self.assertEquals"}
# an exact assertEqual replaced by one of these checks less
UNITTEST_WEAK = {
    "self.assertIn",
    "self.assertIsNotNone",
    "self.assertIsInstance",
    "self.assertGreater",
    "self.assertGreaterEqual",
    "self.assertLess",
    "self.assertLessEqual",
}
UNITTEST_ALMOST = {"self.assertAlmostEqual", "self.assertAlmostEquals"}
UNITTEST_BOUNDS = {
    "self.assertLess": "<",
    "self.assertLessEqual": "<=",
    "self.assertGreater": ">",
    "self.assertGreaterEqual": ">=",
}
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


def _callee(node: Node) -> str:
    """Dotted name of the function a call node calls; "" for any other node."""
    function = node.child_by_field_name("function") if node.type == "call" else None
    return _text(function) if function else ""


def _positional(call: Node) -> list[Node]:
    args = call.child_by_field_name("arguments")
    return [
        a
        for a in (args.named_children if args else [])
        if a.type not in ("keyword_argument", "comment")
    ]


def _asserts(fn: Node) -> list[Node]:
    """`assert` statements and unittest `self.assert*(...)` calls."""
    return [
        n
        for n in _walk(fn)
        if n.type == "assert_statement" or _callee(n).startswith("self.assert")
    ]


def enclosing_test(path: Path, line: int) -> str | None:
    """Name of the test function around `line` (1-based) in `path`, if there is one."""
    if not path.is_file():
        return None
    tree = PARSER.parse(path.read_bytes())
    for node in _walk(tree.root_node):
        name = node.child_by_field_name("name")
        if (
            node.type == "function_definition"
            and name is not None
            and _text(name).startswith("test")
            and node.start_point.row < line <= node.end_point.row + 1
        ):
            return _text(name)
    return None


def source_changed(before_repo: Path, after_repo: Path) -> bool:
    """Whether any non-test .py file differs between the two repos."""

    def sources(repo: Path) -> dict[str, bytes]:
        return {
            f: p.read_bytes()
            for f, p in _py_files(repo).items()
            if not _is_test_file(p)
        }

    # shortcut: repo-wide, any non-test .py counts as "the code under test";
    # resolve the test file's imports if unrelated edits make this noisy.
    return sources(before_repo) != sources(after_repo)


# calls a test uses to set up the world: env vars, attributes, dict entries, mocks
INJECT_CALLS = {
    "monkeypatch.setenv",
    "monkeypatch.setattr",
    "monkeypatch.setitem",
    "os.environ.setdefault",
    "os.putenv",
    "patch",
    "patch.object",
    "patch.dict",
    "mock.patch",
    "mock.patch.object",
    "mock.patch.dict",
}
# literals too common to tie an injection to an assertion
TRIVIAL = {"0", "1", "-1", "True", "False", "None", '""', "''"}


def _injections(fn: Node) -> list[Node]:
    """Setup in a test that plants a value: an injection call or `os.environ[k] = v`.
    shortcut: decorators such as `@patch(...)` are not read; add them when one is seen."""
    found = []
    for n in _walk(fn):
        if n.type == "call" and _callee(n) in INJECT_CALLS:
            found.append(n)
        elif n.type == "assignment":
            left = n.child_by_field_name("left")
            if left is not None and _text(left).startswith("os.environ["):
                found.append(n)
    return found


def _literals(node: Node) -> set[str]:
    return {
        _text(n)
        for n in _walk(node)
        if n.type in ("string", "integer", "float") and _text(n) not in TRIVIAL
    }


def _self_fulfilled(old_fn: Node, fn: Node) -> list[tuple[Node, Node]]:
    """(assert, new injection) pairs: an existing test now plants the very value its
    assertion expects, so the assertion cannot fail any more (a test that needed a
    missing CI secret now sets that secret itself)."""
    old = {_text(n) for n in _injections(old_fn)}
    new = [n for n in _injections(fn) if _text(n) not in old]
    return [
        (assertion, injection)
        for assertion in _asserts(fn)
        for injection in new
        if _literals(assertion) & _literals(injection)
    ]


def _skip_calls(fn: Node) -> list[Node]:
    return [n for n in _walk(fn) if n.type == "call" and _callee(n) in SKIP_CALLS]


EMPTY_ITERABLES = {"[]", "()", "{}", '""', "''", "range(0)", "set()"}


def _dead_loop(node: Node) -> bool:
    """`for _ in []:` / `while False:`: a loop whose body never runs. Loops over real
    data are a legitimate way to check several cases."""
    if node.type == "for_statement":
        iterable = node.child_by_field_name("right")
        return (
            iterable is not None and _text(iterable).replace(" ", "") in EMPTY_ITERABLES
        )
    if node.type == "while_statement":
        condition = node.child_by_field_name("condition")
        return condition is not None and _text(condition) in ("False", "0", "None")
    return False


def _guard(node: Node, fn: Node) -> Node | None:
    """Outermost `if` / `try ... except` / `with suppress(...)` / dead loop that can
    skip `node`."""
    guard = None
    parent = node.parent
    while parent is not None and parent != fn:
        if (
            parent.type == "if_statement"
            or _dead_loop(parent)
            or (
                parent.type == "try_statement"
                and any(c.type.startswith("except") for c in parent.children)
            )
            or (
                parent.type == "with_statement"
                and any(
                    "suppress(" in _text(c)
                    for c in parent.children
                    if c.type == "with_clause"
                )
            )
        ):
            guard = parent
        parent = parent.parent
    return guard


def _equality(assertion: Node) -> list[Node] | None:
    """The two operands of `assert a == b` / `self.assertEqual(a, b)`, else None."""
    if assertion.type == "call":
        args = _positional(assertion)
        equal = _callee(assertion) in UNITTEST_EQUAL and len(args) >= 2
        return args[:2] if equal else None
    cond = assertion.named_children[0]
    if cond.type != "comparison_operator":
        return None
    operators = [o.type for o in cond.children_by_field_name("operators")]
    return cond.named_children if operators == ["=="] else None


def _keyword_numbers(call: Node) -> dict[str, float]:
    found = {}
    args = call.child_by_field_name("arguments")
    for arg in args.named_children if args else []:
        name = arg.child_by_field_name("name")
        value = arg.child_by_field_name("value")
        if arg.type == "keyword_argument" and name and value:
            try:
                found[_text(name)] = float(_text(value))
            except ValueError:
                pass  # not a numeric literal: cannot compare
    return found


def _almost_tolerance(call: Node) -> float | None:
    """Absolute tolerance of `self.assertAlmostEqual(a, b, places=p | delta=d)`."""
    if _callee(call) not in UNITTEST_ALMOST:
        return None
    given = _keyword_numbers(call)
    if "delta" in given:
        return given["delta"]
    places = _positional(call)[2:3]
    try:
        digits = float(_text(places[0])) if places else given.get("places", 7)
    except ValueError:
        return None
    return 0.5 * 10**-digits  # round(a - b, places) == 0


def _tolerance(assertion: Node) -> dict[str, float] | None:
    """Explicit rel= / abs= of the first pytest.approx call; None if there is no call."""
    for node in _walk(assertion):
        callee = node.child_by_field_name("function")
        args = node.child_by_field_name("arguments")
        if node.type != "call" or callee is None or args is None:
            continue
        if _text(callee) not in APPROX_CALLS:
            continue
        return _keyword_numbers(node)
    return None


# bound operators, ranked by how much they admit at the same value
UPPER_BOUNDS = {"<": 0, "<=": 1}
LOWER_BOUNDS = {">": 0, ">=": 1}


def _bound(assertion: Node) -> tuple[str, str, float] | None:
    """(left side, operator, number) of `assert x < 0.5` / `self.assertLess(x, 0.5)`,
    else None."""
    if assertion.type == "call":
        args = _positional(assertion)
        operator = UNITTEST_BOUNDS.get(_callee(assertion))
        if operator is None or len(args) != 2:
            return None
        (left, right), operators = args, [operator]
    else:
        cond = assertion.named_children[0]
        operators = [o.type for o in cond.children_by_field_name("operators")]
        if cond.type != "comparison_operator" or len(operators) != 1:
            return None
        left, right = cond.named_children
    if not _is_literal(right):
        return None
    try:
        return _text(left), operators[0], float(_text(right))
    except ValueError:
        return None  # a string or other non-numeric literal


def _bound_loosened(before: Node, after: Node) -> bool:
    """`x < 0.01` became `x < 1` (or `<=`), or `x >= 0` became `x >= -5`."""
    old, new = _bound(before), _bound(after)
    if old is None or new is None or old[0] != new[0]:
        return False
    for ranks, direction in ((UPPER_BOUNDS, 1), (LOWER_BOUNDS, -1)):
        if old[1] in ranks and new[1] in ranks:
            moved = (new[2] - old[2]) * direction
            return moved > 0 or (moved == 0 and ranks[new[1]] > ranks[old[1]])
    return False


def _weakened(before: Node, after: Node) -> bool:
    if _bound_loosened(before, after):
        return True
    old_almost, new_almost = _almost_tolerance(before), _almost_tolerance(after)
    if old_almost is not None and new_almost is not None:
        same_operands = [_text(a) for a in _positional(before)[:2]] == [
            _text(a) for a in _positional(after)[:2]
        ]
        return same_operands and new_almost > old_almost
    operands = _equality(before)
    if operands is None:
        return False
    texts = {_text(o) for o in operands}
    if after.type == "call":
        args = _positional(after)
        if _callee(after) == "self.assertTrue":
            return bool(args) and _text(args[0]) in texts
        # negated: assertEqual(a, b) became assertNotEqual(a, b)
        if _callee(after) in ("self.assertNotEqual", "self.assertNotEquals"):
            return {_text(a) for a in args[:2]} == texts
        return _callee(after) in UNITTEST_WEAK
    cond = after.named_children[0]
    # truthy-only: `assert x == 5` became `assert x`
    if _text(cond) in texts:
        return True
    if cond.type == "comparison_operator":
        operators = [o.type for o in cond.children_by_field_name("operators")]
        if operators == ["in"]:
            return True
        if operators == ["is not"] and cond.named_children[-1].type == "none":
            return True
        # negated: `assert a == b` became `assert a != b`
        if operators == ["!="] and {_text(o) for o in cond.named_children} == texts:
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

    changed_source = source_changed(before_repo, after_repo)

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
                family: Literal["tampering", "evasion", "faking"] = "tampering",
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
            if relit and changed_source:
                emit(
                    "expected_value_changed",
                    [b for b, _ in relit],
                    [a for _, a in relit],
                    severity="medium",
                )

            planted = _self_fulfilled(old_fn, fn)
            if planted:
                emit(
                    "assertion_self_fulfilled",
                    list({a.start_byte: a for a, _ in planted}.values()),
                    list({i.start_byte: i for _, i in planted}.values()),
                    family="faking",
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
