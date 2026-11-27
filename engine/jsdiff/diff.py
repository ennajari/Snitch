"""Detectors for Jest / Vitest (JS/TS) test files.

Mirrors the Python detectors (engine.astdiff, engine.inventory, engine.rules) on
statically parsed JS/TS trees: the same families, the same pattern names where the
cheat is the same, and the same SnitchEvent shape, so receipts and SARIF mix Python
and JS findings without a format change.
"""

import json
import os
import posixpath
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from tree_sitter import Node

from engine.jsdiff.parse import (
    SKIP_DIRS,
    _text,
    _walk,
    collect_js,
    is_js_test_file,
    js_files,
    parse_tests,
    parser_for,
)
from engine.models import SnitchEvent, new_event

Family = Literal["tampering", "evasion", "faking"]
Severity = Literal["medium", "high"]

# ---------------------------------------------------------------------------
# inventory: which tests exist, which stopped running
# ---------------------------------------------------------------------------

SKIP_MARKS = {"skip", "todo"}


def diff_inventory_js(
    before_repo: Path, after_repo: Path, *, session_id: str = "local"
) -> list[SnitchEvent]:
    """Tests deleted, skipped, or focused (.only) between the two trees. A test whose
    body reappears under another id was renamed or moved, not removed."""
    before = collect_js(before_repo)
    after = collect_js(after_repo)
    before_ids = {i.nodeid for i in before}
    after_by_id = {i.nodeid: i for i in after}
    now = datetime.now(UTC)

    def event(
        family: Literal["tampering", "evasion"],
        pattern: str,
        nodeid: str,
        file: str,
        line_start: int,
        line_end: int,
        after_text: str | None,
        severity: Severity = "high",
    ) -> SnitchEvent:
        return new_event(
            session_id=session_id,
            family=family,
            pattern=pattern,
            severity=severity,
            nodeid=nodeid,
            file=file,
            line_start=line_start,
            line_end=line_end,
            before=nodeid if family == "tampering" else None,
            after=after_text,
            detector="inventory",
            created_at=now,
        )

    events: list[SnitchEvent] = []
    new_items = [i for i in after if i.nodeid not in before_ids and i.body_hash]
    for item in before:
        kept = after_by_id.get(item.nodeid)
        if kept is not None:
            added = sorted(SKIP_MARKS & (set(kept.markers) - set(item.markers)))
            if added:
                events.append(
                    event(
                        "evasion",
                        "test_skipped",
                        kept.nodeid,
                        kept.file,
                        kept.line_start,
                        kept.line_end,
                        ",".join(added),
                    )
                )
            if "only" in kept.markers and "only" not in item.markers:
                # .only silences every other test of the file when the runner honors it
                events.append(
                    event(
                        "evasion",
                        "test_focused",
                        kept.nodeid,
                        kept.file,
                        kept.line_start,
                        kept.line_end,
                        "only",
                        "medium",
                    )
                )
        else:
            twins = [i for i in new_items if i.body_hash == item.body_hash]
            if twins:
                new_items.remove(twins[0])  # renamed or moved, body intact: fine
                continue
            events.append(
                event(
                    "tampering",
                    "test_deleted",
                    item.nodeid,
                    item.file,
                    item.line_start,
                    item.line_end,
                    None,
                )
            )
    return events


# ---------------------------------------------------------------------------
# assertion diff: what the surviving tests now claim
# ---------------------------------------------------------------------------

EXACT_MATCHERS = {"toBe", "toEqual", "toStrictEqual"}
# what an exact check can be swapped for while admitting strictly more values
WEAK_MATCHERS = {
    "toBeTruthy",
    "toBeDefined",
    "toBeInstanceOf",
    "toContain",
    "toContainEqual",
    "toMatch",
    "toMatchObject",
    "toBeCloseTo",
    "toHaveLength",
}
# toBe and toStrictEqual both pin types; toEqual drops that
STRICTNESS = {"toStrictEqual": 2, "toBe": 2, "toEqual": 1}
UPPER_BOUNDS = {"toBeLessThan": 0, "toBeLessThanOrEqual": 1}
LOWER_BOUNDS = {"toBeGreaterThan": 0, "toBeGreaterThanOrEqual": 1}
THROW_MATCHERS = {"toThrow", "toThrowError"}
CALL_ARGS_MATCHERS = {"toHaveBeenCalledWith", "toHaveReturnedWith"}
WEAK_CALL_MATCHERS = {"toHaveBeenCalled", "toHaveReturned", "toHaveBeenCalledTimes"}
LITERAL_TYPES = {"number", "string", "true", "false", "null", "undefined", "regex"}


@dataclass
class JsAssert:
    node: Node  # the whole `expect(actual).matcher(...)` call
    actual: Node | None  # None for expect.assertions(...) / expect.hasAssertions()
    modifiers: list[str]  # not / resolves / rejects, in source order
    matcher: str
    args: list[Node]
    text: str


def _expect_chain(call: Node) -> JsAssert | None:
    """The assertion a call expression makes, or None."""
    node = call.child_by_field_name("function")
    chain: list[str] = []
    while node is not None and node.type == "member_expression":
        prop = node.child_by_field_name("property")
        if prop is None:
            return None
        chain.append(_text(prop))
        node = node.child_by_field_name("object")
    actual: Node | None = None
    if node is not None and node.type == "call_expression":
        inner = node.child_by_field_name("function")
        if inner is None or inner.type != "identifier" or _text(inner) != "expect":
            return None
        inner_args = node.child_by_field_name("arguments")
        actuals = list(inner_args.named_children) if inner_args else []
        actual = actuals[0] if actuals else None
    elif not (
        node is not None and node.type == "identifier" and _text(node) == "expect"
    ):
        return None
    if not chain:
        return None  # bare expect(x), not an assertion
    chain.reverse()
    args_node = call.child_by_field_name("arguments")
    args = list(args_node.named_children) if args_node else []
    return JsAssert(
        node=call,
        actual=actual,
        modifiers=chain[:-1],
        matcher=chain[-1],
        args=args,
        text=_text(call),
    )


def _asserts(body: Node) -> list[JsAssert]:
    return [
        found
        for n in _walk(body)
        if n.type == "call_expression" and (found := _expect_chain(n)) is not None
    ]


def _is_literal(node: Node) -> bool:
    if node.type == "unary_expression":
        children = node.named_children
        return len(children) == 1 and children[0].type == "number"
    return node.type in LITERAL_TYPES


def _number(node: Node | None) -> float | None:
    if node is None or not _is_literal(node):
        return None
    try:
        return float(_text(node))
    except ValueError:
        return None


def _same_operands(before: JsAssert, after: JsAssert) -> bool:
    return (
        before.actual is not None
        and after.actual is not None
        and _text(before.actual) == _text(after.actual)
        and [_text(a) for a in before.args] == [_text(a) for a in after.args]
    )


def _weakened(before: JsAssert, after: JsAssert) -> bool:
    """Whether `after` checks strictly less than `before` did."""
    b, a = before, after
    # negated: expect(x).toBe(5) became expect(x).not.toBe(5)
    if (
        b.matcher == a.matcher
        and "not" not in b.modifiers
        and "not" in a.modifiers
        and _same_operands(b, a)
    ):
        return True
    # inverted actual: expect(x).toBe(true) became expect(!x).toBe(true)
    if (
        b.matcher == a.matcher
        and b.actual is not None
        and a.actual is not None
        and a.actual.type == "unary_expression"
        and _text(a.actual).replace(" ", "").startswith("!")
        and a.actual.named_children
        and _text(a.actual.named_children[0]) == _text(b.actual)
        and [_text(x) for x in b.args] == [_text(x) for x in a.args]
    ):
        return True
    # an exact check swapped for one that admits more values
    if b.matcher in EXACT_MATCHERS and a.matcher in WEAK_MATCHERS:
        return True
    if b.matcher in STRICTNESS and a.matcher in STRICTNESS:
        return STRICTNESS[b.matcher] > STRICTNESS[a.matcher]
    # expect(fn).toHaveBeenCalledWith("a", 1) became toHaveBeenCalled()
    if b.matcher in CALL_ARGS_MATCHERS and a.matcher in WEAK_CALL_MATCHERS:
        return True
    # bound loosened: toBeLessThan(0.01) became toBeLessThan(1) (or <= at 0.01)
    for ranks, direction in ((UPPER_BOUNDS, 1), (LOWER_BOUNDS, -1)):
        if b.matcher in ranks and a.matcher in ranks:
            if (
                b.actual is None
                or a.actual is None
                or _text(b.actual) != _text(a.actual)
            ):
                return False
            old = _number(b.args[0] if b.args else None)
            new = _number(a.args[0] if a.args else None)
            if old is None or new is None:
                return False
            moved = (new - old) * direction
            return moved > 0 or (moved == 0 and ranks[a.matcher] > ranks[b.matcher])
    # toThrow("boom") became toThrow(): any error passes
    return bool(
        b.matcher in THROW_MATCHERS
        and a.matcher in THROW_MATCHERS
        and b.args
        and not a.args
    )


def _literal_changed(before: JsAssert, after: JsAssert) -> bool:
    """A literal operand of an exact check was edited (the expected value retuned)."""
    b, a = before, after
    if b.matcher != a.matcher or b.matcher not in EXACT_MATCHERS | CALL_ARGS_MATCHERS:
        return False
    pairs: list[tuple[Node | None, Node | None]] = [(b.actual, a.actual)]
    pairs += list(zip(b.args, a.args, strict=False))
    return any(
        o is not None
        and n is not None
        and _is_literal(o)
        and _is_literal(n)
        and _text(o) != _text(n)
        for o, n in pairs
    )


def _rewritten(before: JsAssert, after: JsAssert) -> bool:
    """The expected literal stays, but the actual side is wrapped until it matches:
    expect(f(x)).toBe(19800) became expect(f(x) * 60).toBe(19800)."""
    b, a = before, after
    if b.matcher != a.matcher or b.matcher not in EXACT_MATCHERS:
        return False
    if not b.args or not a.args or b.actual is None or a.actual is None:
        return False
    expected, new_expected = b.args[0], a.args[0]
    if not _is_literal(expected) or _text(new_expected) != _text(expected):
        return False
    old, new = _text(b.actual), _text(a.actual)
    return old != new and old in new


def _dead_loop(node: Node) -> bool:
    """`while (false)` / `for (...; false; ...)`: a body that never runs."""
    if node.type not in ("while_statement", "for_statement"):
        return False
    condition = node.child_by_field_name("condition")
    return condition is not None and _text(condition).strip() in ("false", "0")


def _guard(node: Node, body: Node) -> Node | None:
    """Outermost `if` / `try ... catch` / dead loop that can skip `node`."""
    guard = None
    parent = node.parent
    while parent is not None and parent != body:
        if (
            parent.type == "if_statement"
            or _dead_loop(parent)
            or (
                parent.type == "try_statement"
                and any(c.type == "catch_clause" for c in parent.children)
            )
        ):
            guard = parent
        parent = parent.parent
    return guard


def _loop_bounds(body: Node) -> list[tuple[Node, str, float]]:
    """(for statement, `i<`, bound) for `for (...; i < N; ...)` with N a literal."""
    found = []
    for n in _walk(body):
        if n.type != "for_statement":
            continue
        cond = n.child_by_field_name("condition")
        if cond is None or cond.type != "binary_expression":
            continue
        left = cond.child_by_field_name("left")
        right = cond.child_by_field_name("right")
        operators = [c.type for c in cond.children if c.type in ("<", "<=", ">", ">=")]
        if left is None or left.type != "identifier" or len(operators) != 1:
            continue
        value = _number(right)
        if value is not None:
            found.append((n, f"{_text(left)}{operators[0]}", value))
    return found


def _imports(root: Node) -> dict[str, set[str]]:
    """Module specifier -> the local names imported from it (ES imports only;
    shortcut: destructured require() is not read)."""
    found: dict[str, set[str]] = {}
    for n in _walk(root):
        if n.type != "import_statement":
            continue
        source = n.child_by_field_name("source")
        if source is None:
            continue
        spec = _text(source).strip("'\"")
        names: set[str] = set()
        for node in _walk(n):
            if node.type == "import_specifier":
                local = node.child_by_field_name("alias") or node.child_by_field_name(
                    "name"
                )
                if local is not None:
                    names.add(_text(local))
            elif node.type in ("namespace_import", "import_clause"):
                for child in node.named_children:
                    if child.type == "identifier":
                        names.add(_text(child))
        found.setdefault(spec, set()).update(names)
    return found


MOCK_CALLS = {("jest", "mock"), ("vi", "mock")}


def _module_mocks(root: Node) -> list[tuple[Node, str]]:
    """(call, specifier) for each jest.mock("./mod") / vi.mock("./mod")."""
    found = []
    for n in _walk(root):
        if n.type != "call_expression":
            continue
        fn = n.child_by_field_name("function")
        if fn is None or fn.type != "member_expression":
            continue
        obj = fn.child_by_field_name("object")
        prop = fn.child_by_field_name("property")
        if obj is None or prop is None or obj.type != "identifier":
            continue
        if (_text(obj), _text(prop)) not in MOCK_CALLS:
            continue
        args_node = n.child_by_field_name("arguments")
        args = list(args_node.named_children) if args_node else []
        if args and args[0].type == "string":
            found.append((n, _text(args[0]).strip("'\"")))
    return found


def _resolve(test_file: str, spec: str, files: dict[str, Path]) -> str | None:
    """Repo-relative path a relative import points at, if it is a repo file."""
    if not spec.startswith("."):
        return None
    base = posixpath.normpath(posixpath.join(posixpath.dirname(test_file), spec))
    suffixes = [".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".mjs", ".cjs"]
    candidates = (
        [base] + [base + s for s in suffixes] + [f"{base}/index{s}" for s in suffixes]
    )
    return next((c for c in candidates if c in files), None)


def _pair(
    before: list[JsAssert], after: list[JsAssert]
) -> tuple[
    list[tuple[JsAssert, JsAssert]], list[tuple[JsAssert, JsAssert]], list[JsAssert]
]:
    """Split asserts into (unchanged pairs, changed pairs, removed), by exact text."""
    by_text: dict[str, list[JsAssert]] = {}
    for assertion in after:
        by_text.setdefault(assertion.text, []).append(assertion)
    same, rest_before = [], []
    for assertion in before:
        twins = by_text.get(assertion.text)
        if twins:
            same.append((assertion, twins.pop(0)))
        else:
            rest_before.append(assertion)
    rest_after = sorted(
        (a for nodes in by_text.values() for a in nodes),
        key=lambda a: a.node.start_byte,
    )
    changed = list(zip(rest_before, rest_after, strict=False))
    return same, changed, rest_before[len(rest_after) :]


def js_source_changed(before_repo: Path, after_repo: Path) -> bool:
    """Whether any non-test JS/TS file differs between the two repos."""

    def sources(repo: Path) -> dict[str, bytes]:
        return {
            f: p.read_bytes()
            for f, p in js_files(repo).items()
            if not is_js_test_file(p)
        }

    # shortcut: repo-wide, any non-test JS/TS file counts as "the code under test"
    return sources(before_repo) != sources(after_repo)


def diff_ast_js(
    before_repo: Path, after_repo: Path, *, session_id: str = "local"
) -> list[SnitchEvent]:
    before_files = js_files(before_repo)
    after_files = js_files(after_repo)
    now = datetime.now(UTC)
    changed_source = js_source_changed(before_repo, after_repo)

    events: list[SnitchEvent] = []

    def emit(
        pattern: str,
        befores: list[Node],
        afters: list[Node],
        *,
        family: Family = "tampering",
        severity: Severity = "high",
        span: list[Node],
        nodeid: str,
        file: str,
    ) -> None:
        nodes = span or afters or befores
        events.append(
            new_event(
                session_id=session_id,
                family=family,
                pattern=pattern,
                severity=severity,
                nodeid=nodeid,
                file=file,
                line_start=min(n.start_point.row for n in nodes) + 1,
                line_end=max(n.end_point.row for n in nodes) + 1,
                before="\n".join(map(_text, befores)) or None,
                after="\n".join(map(_text, afters)) or None,
                detector="ast",
                created_at=now,
            )
        )

    for file, after_path in after_files.items():
        before_path = before_files.get(file)
        if (
            before_path is None
            or not is_js_test_file(after_path)
            or before_path.read_bytes() == after_path.read_bytes()
        ):
            continue
        # Trees must outlive their nodes.
        before_tree = parser_for(before_path).parse(before_path.read_bytes())
        after_tree = parser_for(after_path).parse(after_path.read_bytes())
        before_tests = {t.nodeid: t for t in parse_tests(before_path, before_repo)}
        after_tests = {t.nodeid: t for t in parse_tests(after_path, after_repo)}

        # Asserts of tests that are new in this file: a "removed" assert found here
        # was moved by a test split, not dropped.
        moved = {
            a.text
            for nodeid, test in after_tests.items()
            if nodeid not in before_tests and test.body is not None
            for a in _asserts(test.body)
        }

        # mocking the very module the test asserts on checks the stand-in, not the code
        old_mocks = {_text(c) for c, _ in _module_mocks(before_tree.root_node)}
        imported = _imports(after_tree.root_node)
        for call, spec in _module_mocks(after_tree.root_node):
            if _text(call) in old_mocks:
                continue
            resolved = _resolve(file, spec, after_files)
            if resolved is None or is_js_test_file(after_files[resolved]):
                continue
            names = imported.get(spec, set())
            if not names:
                continue
            uses = [
                nodeid
                for nodeid, test in after_tests.items()
                if test.body is not None
                for a in _asserts(test.body)
                if a.actual is not None
                and any(
                    re.search(rf"\b{re.escape(name)}\b", _text(a.actual))
                    for name in names
                )
            ]
            if uses:
                emit(
                    "mock_code_under_test",
                    [],
                    [call],
                    family="faking",
                    span=[call],
                    nodeid=uses[0],
                    file=file,
                )

        for nodeid, test in after_tests.items():
            old_test = before_tests.get(nodeid)
            if old_test is None or test.body is None or old_test.body is None:
                continue
            body: Node = test.body
            old_body: Node = old_test.body

            def emit_test(
                pattern: str,
                befores: list[Node],
                afters: list[Node],
                *,
                family: Family = "tampering",
                severity: Severity = "high",
                span: list[Node] | None = None,
                nodeid: str = nodeid,
                file: str = file,
                body: Node = body,
            ) -> None:
                emit(
                    pattern,
                    befores,
                    afters,
                    family=family,
                    severity=severity,
                    span=span or afters or [body],
                    nodeid=nodeid,
                    file=file,
                )

            same, changed, removed = _pair(_asserts(old_body), _asserts(body))
            dropped = [a for a in removed if a.text not in moved]
            if dropped:
                emit_test("assertion_removed", [a.node for a in dropped], [])

            weakened = [(b, a) for b, a in changed if _weakened(b, a)]
            if weakened:
                emit_test(
                    "assertion_weakened",
                    [b.node for b, _ in weakened],
                    [a.node for _, a in weakened],
                )

            relit = [
                (b, a)
                for b, a in changed
                if (b, a) not in weakened and _literal_changed(b, a)
            ]
            if relit and changed_source:
                emit_test(
                    "expected_value_changed",
                    [b.node for b, _ in relit],
                    [a.node for _, a in relit],
                    severity="medium",
                )

            rewritten = [
                (b, a)
                for b, a in changed
                if (b, a) not in weakened and _rewritten(b, a)
            ]
            if rewritten:
                emit_test(
                    "assertion_rewritten",
                    [b.node for b, _ in rewritten],
                    [a.node for _, a in rewritten],
                    severity="medium",
                )

            shrunk = [
                (b, a)
                for (b, old_key, old), (a, new_key, new) in zip(
                    _loop_bounds(old_body), _loop_bounds(body), strict=False
                )
                if old_key == new_key and new * 10 <= old
            ]
            if shrunk:
                emit_test(
                    "test_scope_reduced",
                    [b for b, _ in shrunk],
                    [a for _, a in shrunk],
                    severity="medium",
                )

            guarded = [
                (b, guard)
                for b, a in same + changed
                if _guard(b.node, old_body) is None
                and (guard := _guard(a.node, body)) is not None
            ]
            if guarded:
                emit_test(
                    "assertion_guarded",
                    [b.node for b, _ in guarded],
                    # two asserts under one guard report that guard once
                    list({g.start_byte: g for _, g in guarded}.values()),
                )
    return events


# ---------------------------------------------------------------------------
# rules: the runner and package configuration
# ---------------------------------------------------------------------------

JS_CONFIGS = {
    "jest.config.js",
    "jest.config.cjs",
    "jest.config.mjs",
    "jest.config.ts",
    "jest.config.json",
    "vitest.config.js",
    "vitest.config.mjs",
    "vitest.config.ts",
    "vitest.config.mts",
}
JS_RUNNER = re.compile(r"\b(jest|vitest|mocha|jasmine|ava|tap|node\s+--test)\b")
PASS_WITH_NO_TESTS = re.compile(r"passWithNoTests\s*:\s*true|--passWithNoTests\b")
IGNORE_PATTERNS = re.compile(r"(testPathIgnorePatterns|coveragePathIgnorePatterns)\s*:")
OR_TRUE = re.compile(r"\|\|\s*(true|:|echo\b)")
COVERAGE_KEYS = re.compile(
    r"['\"]?(statements|branches|functions|lines)['\"]?\s*:\s*(-?\d+(?:\.\d+)?)"
)


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
        if (text := line.strip()) and text not in old and not text.startswith("//")
    ]


def _json(path: Path | None) -> dict[str, object] | None:
    """The parsed config, None when missing or invalid (invalid = the runner fails)."""
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(_read(path))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _as_str_list(value: object) -> list[str]:
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _coverage_thresholds(config: dict[str, object]) -> dict[str, float]:
    """coverageThreshold leaves, keyed by `scope.key` (`global.lines`)."""
    threshold = config.get("coverageThreshold")
    if not isinstance(threshold, dict):
        return {}
    found: dict[str, float] = {}
    for scope, values in threshold.items():
        if not isinstance(values, dict):
            continue
        for key, value in values.items():
            if isinstance(value, int | float):
                found[f"{scope}.{key}"] = float(value)
    return found


def _script_thresholds(text: str) -> dict[str, float]:
    """coverageThreshold numbers in a .js/.ts config, read as text.

    shortcut: the block is found by brace matching from the word itself; a computed
    threshold (`isCI ? 80 : 0`) is not a number literal and is not compared."""
    start = text.find("coverageThreshold")
    if start < 0:
        return {}
    open_brace = text.find("{", start)
    if open_brace < 0:
        return {}
    depth, end = 0, len(text)
    for i in range(open_brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    return {
        key: float(value) for key, value in COVERAGE_KEYS.findall(text[open_brace:end])
    }


def _js_configs(repo: Path) -> dict[str, Path]:
    """package.json and jest/vitest config files, at any depth, deps pruned."""
    found: dict[str, Path] = {}
    for base, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in sorted(files):
            if name == "package.json" or name in JS_CONFIGS:
                path = Path(base) / name
                found[path.relative_to(repo).as_posix()] = path
    return dict(sorted(found.items()))


def diff_rules_js(
    before_repo: Path, after_repo: Path, *, session_id: str = "local"
) -> list[SnitchEvent]:
    """Runner-config edits that make a failing or absent suite look green."""
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
        severity: Severity = "high",
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

    def line_of(path: Path, pattern: re.Pattern[str]) -> int:
        for number, text in enumerate(_read(path).splitlines(), 1):
            if pattern.search(text):
                return number
        return 1

    for file, after_path in _js_configs(after_repo).items():
        before_path = before_repo / file
        if (
            not before_path.is_file()
            or before_path.read_bytes() == after_path.read_bytes()
        ):
            continue  # a new config is setup, not an edit; unchanged cannot fire

        def lowered(
            old: dict[str, float],
            new: dict[str, float],
            file: str = file,
            after_path: Path = after_path,
        ) -> None:
            dropped = [k for k in old if k not in new or new[k] < old[k]]
            if dropped:
                emit(
                    "tampering",
                    "coverage_threshold_lowered",
                    file,
                    line_of(after_path, re.compile(r"coverageThreshold")),
                    line_of(after_path, re.compile(r"coverageThreshold")),
                    ", ".join(f"{k}={old[k]:g}" for k in dropped),
                    ", ".join(
                        "removed" if k not in new else f"{k}={new[k]:g}"
                        for k in dropped
                    ),
                )

        if after_path.name == "package.json":
            old, new = _json(before_path), _json(after_path)
            if old is None or new is None:
                continue
            old_scripts = old.get("scripts")
            new_scripts = new.get("scripts")
            old_test = (
                old_scripts.get("test") if isinstance(old_scripts, dict) else None
            )
            new_test = (
                new_scripts.get("test") if isinstance(new_scripts, dict) else None
            )
            if isinstance(old_test, str) and JS_RUNNER.search(old_test):
                line = line_of(after_path, re.compile(r'"test"\s*:'))
                if not isinstance(new_test, str) or not JS_RUNNER.search(new_test):
                    # the test script no longer runs a test runner at all
                    emit(
                        "evasion",
                        "test_script_weakened",
                        file,
                        line,
                        line,
                        old_test,
                        new_test if isinstance(new_test, str) else None,
                    )
                else:
                    words = [w for w in new_test.split() if w not in old_test.split()]
                    if any(PASS_WITH_NO_TESTS.search(w) for w in words):
                        emit(
                            "evasion",
                            "pass_with_no_tests",
                            file,
                            line,
                            line,
                            old_test,
                            new_test,
                        )
                    if OR_TRUE.search(new_test) and not OR_TRUE.search(old_test):
                        emit(
                            "evasion",
                            "ci_or_true",
                            file,
                            line,
                            line,
                            old_test,
                            new_test,
                        )
            old_jest = old.get("jest")
            new_jest = new.get("jest")
            old_cfg = old_jest if isinstance(old_jest, dict) else None
            new_cfg = new_jest if isinstance(new_jest, dict) else None
        elif after_path.name.endswith(".json"):
            old_cfg = _json(before_path) or {}
            new_cfg = _json(after_path) or {}
        else:  # a .js/.ts config: line-based, like the CI rules
            added = _added(before_path, after_path)
            hits = [h for h in added if PASS_WITH_NO_TESTS.search(h[1])]
            if hits:
                emit(
                    "evasion",
                    "pass_with_no_tests",
                    file,
                    hits[0][0],
                    hits[-1][0],
                    None,
                    "\n".join(text for _, text in hits),
                )
            hits = [h for h in added if IGNORE_PATTERNS.search(h[1])]
            if hits:
                emit(
                    "evasion",
                    "test_paths_ignored",
                    file,
                    hits[0][0],
                    hits[-1][0],
                    None,
                    "\n".join(text for _, text in hits),
                    "medium",
                )
            lowered(
                _script_thresholds(_read(before_path)),
                _script_thresholds(_read(after_path)),
            )
            continue

        # JSON-shaped configs: the jest key of package.json, or jest.config.json
        if old_cfg or new_cfg:
            old_cfg, new_cfg = old_cfg or {}, new_cfg or {}
            if not old_cfg.get("passWithNoTests") and new_cfg.get("passWithNoTests"):
                line = line_of(after_path, re.compile(r"passWithNoTests"))
                emit(
                    "evasion",
                    "pass_with_no_tests",
                    file,
                    line,
                    line,
                    None,
                    "passWithNoTests: true",
                )
            old_ignores = set(_as_str_list(old_cfg.get("testPathIgnorePatterns")))
            new_ignores = set(_as_str_list(new_cfg.get("testPathIgnorePatterns")))
            if old_cfg and new_ignores - old_ignores:
                line = line_of(after_path, re.compile(r"testPathIgnorePatterns"))
                emit(
                    "evasion",
                    "test_paths_ignored",
                    file,
                    line,
                    line,
                    ", ".join(sorted(old_ignores)) or None,
                    ", ".join(sorted(new_ignores)),
                    "medium",
                )
            lowered(_coverage_thresholds(old_cfg), _coverage_thresholds(new_cfg))
    return events


def diff_js(
    before_repo: Path, after_repo: Path, *, session_id: str = "local"
) -> list[SnitchEvent]:
    """All JS/TS detectors, fully static (no node, no runner, no network)."""
    return (
        diff_inventory_js(before_repo, after_repo, session_id=session_id)
        + diff_ast_js(before_repo, after_repo, session_id=session_id)
        + diff_rules_js(before_repo, after_repo, session_id=session_id)
    )
