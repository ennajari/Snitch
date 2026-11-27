"""Static parsing of Jest / Vitest test files (no node, no test run).

The Python detectors collect the inventory by running pytest; a JS repo may have no
node_modules installed (a session baseline never does), so the JS side parses the
test files with tree-sitter instead. shortcut: discovery uses the conventional
names (`*.test.*`, `*.spec.*`, `__tests__/`), not each runner's `testMatch` /
`include` config; a config that renames test files is a rules-detector job.
"""

import hashlib
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter_javascript
import tree_sitter_typescript
from tree_sitter import Language, Node, Parser

PARSERS = {
    "js": Parser(Language(tree_sitter_javascript.language())),
    "ts": Parser(Language(tree_sitter_typescript.language_typescript())),
    "tsx": Parser(Language(tree_sitter_typescript.language_tsx())),
}


def parser_for(path: Path) -> Parser:
    if path.suffix in (".ts", ".mts", ".cts"):
        return PARSERS["ts"]
    if path.suffix == ".tsx":
        return PARSERS["tsx"]
    return PARSERS["js"]  # .js, .mjs, .cjs, .jsx (the grammar covers JSX)


JS_EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "coverage"}


def is_js_test_file(path: Path) -> bool:
    """`foo.test.ts`, `foo.spec.jsx`, or anything under a `__tests__` folder."""
    if path.suffix not in JS_EXTENSIONS or path.name.endswith(".d.ts"):
        return False
    if any(
        path.name.endswith(f"{marker}{path.suffix}") for marker in (".test", ".spec")
    ):
        return True
    return "__tests__" in path.parts


def js_files(repo: Path) -> dict[str, Path]:
    """Repo-relative posix path -> path for every JS/TS file, skipping dependency
    and build folders. os.walk so `node_modules` is pruned, never walked."""
    found: dict[str, Path] = {}
    for base, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in sorted(files):
            path = Path(base) / name
            if path.suffix in JS_EXTENSIONS and not name.endswith(".d.ts"):
                found[path.relative_to(repo).as_posix()] = path
    return dict(sorted(found.items()))


def _text(node: Node) -> str:
    return (node.text or b"").decode()


def _walk(node: Node) -> Iterator[Node]:
    yield node
    for child in node.children:
        yield from _walk(child)


def _fingerprint(node: Node) -> str:
    """Structure + leaf text of a test body: a rename of the test keeps the hash."""
    parts: list[str] = []

    def dump(n: Node) -> None:
        parts.append(n.type)
        if n.child_count == 0:
            parts.append(_text(n))
            return
        for c in n.children:
            dump(c)

    dump(node)
    return hashlib.sha1("\0".join(parts).encode()).hexdigest()


TEST_BASES = {"describe", "it", "test"}
BARE_SKIP = {"xit", "xtest", "xdescribe"}
BARE_ONLY = {"fit", "fdescribe"}
SKIP_PROPS = {"skip", "todo"}
CONTAINER_PROPS = {"skip", "only", "each", "concurrent"}


def _callee(call: Node) -> tuple[str, list[str]] | None:
    """(base, property chain) of a test declaration call: `it.skip(...)` ->
    ("it", ["skip"]), `test.each(cases)(...)` -> ("test", ["each"])."""
    fn = call.child_by_field_name("function")
    while fn is not None and fn.type == "call_expression":
        fn = fn.child_by_field_name("function")  # the applied table of .each(...)
    props: list[str] = []
    while fn is not None and fn.type == "member_expression":
        prop = fn.child_by_field_name("property")
        if prop is None:
            return None
        props.append(_text(prop))
        fn = fn.child_by_field_name("object")
    if fn is None or fn.type != "identifier":
        return None
    base = _text(fn)
    if base not in TEST_BASES | BARE_SKIP | BARE_ONLY:
        return None
    return base, list(reversed(props))


def _string_arg(node: Node) -> str:
    """The test name: the string's content, else the raw source of the argument."""
    if node.type == "string":
        fragment = next(
            (c for c in node.named_children if c.type == "string_fragment"), None
        )
        return _text(fragment) if fragment is not None else _text(node)
    return _text(node)


@dataclass
class JsTest:
    nodeid: str
    file: str
    line_start: int
    line_end: int
    name: str
    markers: list[str]
    body_hash: str | None
    body: Node | None = field(default=None, repr=False)

    def item(self) -> "JsItem":
        return JsItem(
            nodeid=self.nodeid,
            file=self.file,
            line_start=self.line_start,
            line_end=self.line_end,
            name=self.name,
            markers=self.markers,
            body_hash=self.body_hash,
        )


@dataclass
class JsItem:
    """The serializable part of JsTest (mirrors inventory.collect.Item)."""

    nodeid: str
    file: str
    line_start: int
    line_end: int
    name: str
    markers: list[str]
    body_hash: str | None


def _declaration(call: Node) -> tuple[str, list[str], list[Node]] | None:
    """(base, props, arguments) if `call` declares tests, else None."""
    found = _callee(call)
    if found is None:
        return None
    base, props = found
    args_node = call.child_by_field_name("arguments")
    return base, props, list(args_node.named_children) if args_node else []


def _callback(args: list[Node]) -> Node | None:
    return next(
        (a for a in args if a.type in ("arrow_function", "function_expression")), None
    )


def _scan(
    node: Node, prefix: list[str], markers: list[str], out: list[JsTest], file: str
) -> None:
    """Tests declared at this level and inside `describe` callbacks.

    shortcut: tests generated in helper functions or loops are not seen; suites in
    the wild declare them at statement level or nested in describes."""
    for child in node.named_children:
        target = child
        if child.type == "expression_statement" and child.named_children:
            target = child.named_children[0]
        if target.type != "call_expression":
            continue
        decl = _declaration(target)
        if decl is None:
            continue
        base, props, args = decl
        if not args:
            continue
        name = _string_arg(args[0])
        marks = list(markers)
        if base in BARE_SKIP or SKIP_PROPS & set(props):
            marks.append("todo" if "todo" in props else "skip")
        if base in BARE_ONLY or "only" in props:
            marks.append("only")
        callback = _callback(args[1:])
        body = callback.child_by_field_name("body") if callback is not None else None
        is_container = base in ("describe", "xdescribe", "fdescribe")
        if callback is None and not is_container:
            marks.append("todo")  # `it("name")`: a pending test, it never runs
        if not is_container:
            nodeid = f"{file}::{' > '.join([*prefix, name])}"
            out.append(
                JsTest(
                    nodeid=nodeid,
                    file=file,
                    line_start=target.start_point.row + 1,
                    line_end=target.end_point.row + 1,
                    name=name,
                    markers=sorted(set(marks)),
                    body_hash=_fingerprint(body) if body is not None else None,
                    body=body,
                )
            )
        if is_container and body is not None:
            _scan(body, [*prefix, name], marks, out, file)


def parse_tests(path: Path, repo: Path) -> list[JsTest]:
    """Every test declared in one file, describe-nesting folded into the nodeid."""
    rel = path.relative_to(repo).as_posix()
    tree = parser_for(path).parse(path.read_bytes())
    out: list[JsTest] = []
    _scan(tree.root_node, [], [], out, rel)
    return out


def collect_js(repo: Path) -> list[JsItem]:
    items: list[JsItem] = []
    for path in js_files(repo).values():
        if is_js_test_file(path):
            items.extend(t.item() for t in parse_tests(path, repo))
    return items


def enclosing_test_js(path: Path, line: int) -> str | None:
    """The `describe > ... > it` id of the test around `line` (1-based), if any."""
    if not path.is_file():
        return None
    tree = parser_for(path).parse(path.read_bytes())
    out: list[JsTest] = []
    _scan(tree.root_node, [], [], out, path.name)
    for test in out:
        if test.line_start <= line <= test.line_end:
            return test.nodeid.split("::", 1)[1]
    return None
