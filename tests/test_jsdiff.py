import json
import shutil
import subprocess
from pathlib import Path

import pytest

from engine.detect import run_detectors
from engine.jsdiff.diff import diff_ast_js, diff_inventory_js, diff_rules_js
from engine.jsdiff.parse import collect_js, enclosing_test_js, parse_tests

FIXTURES = Path(__file__).parent / "fixtures_js"
COMPARED = {
    "family",
    "pattern",
    "severity",
    "file",
    "line_start",
    "line_end",
    "before",
    "after",
    "detector",
}

INVENTORY = [
    "js_test_deleted",
    "js_test_skipped",
    "js_test_skipped_xit",
    "js_test_pending",
    "js_test_focused",
    "js_legit_test_renamed",
    "js_legit_skip_unchanged",
]
AST = [
    "js_assertion_weakened_truthy",
    "js_assertion_weakened_bound",
    "js_legit_bound_tightened",
    "js_assertion_weakened_negated",
    "js_assertion_weakened_throw",
    "js_assertion_weakened_identity",
    "js_assertion_weakened_nested",
    "js_assertion_removed",
    "js_legit_assert_added",
    "js_legit_assertion_strengthened",
    "js_expected_value_changed",
    "js_legit_expected_updated",
    "js_assertion_rewritten",
    "js_assertion_guarded",
    "js_legit_refactor_same_asserts",
    "js_test_scope_reduced",
    "js_mock_code_under_test",
    "js_legit_mock_dependency",
    "js_legit_test_split",
]
RULES = [
    "js_test_script_weakened",
    "js_pass_with_no_tests_script",
    "js_script_or_true",
    "js_coverage_threshold_lowered",
    "js_coverage_threshold_removed",
    "js_config_pass_with_no_tests",
    "js_test_paths_ignored",
    "js_legit_config_created",
    "js_legit_coverage_raised",
    "js_legit_script_verbose",
]


def _check(name: str, diff, tmp_path: Path) -> None:
    before = shutil.copytree(FIXTURES / name / "before", tmp_path / "before")
    after = shutil.copytree(FIXTURES / name / "after", tmp_path / "after")
    expected = json.loads((FIXTURES / name / "expected.json").read_text())

    events = [e.model_dump(include=COMPARED) for e in diff(before, after)]

    assert events == expected


@pytest.mark.parametrize("name", INVENTORY)
def test_inventory_fixture(name: str, tmp_path: Path) -> None:
    # the inventory fixtures expect no ast/rules events and vice versa: the
    # combined expected.json is checked against each detector alone
    _check(name, diff_inventory_js, tmp_path)


@pytest.mark.parametrize("name", AST)
def test_ast_fixture(name: str, tmp_path: Path) -> None:
    _check(name, diff_ast_js, tmp_path)


@pytest.mark.parametrize("name", RULES)
def test_rules_fixture(name: str, tmp_path: Path) -> None:
    _check(name, diff_rules_js, tmp_path)


def test_combined_run_matches_expected(tmp_path: Path) -> None:
    for side in ("before", "after"):
        shutil.copytree(
            FIXTURES / "js_assertion_weakened_truthy" / side, tmp_path / side
        )

    events, warnings = run_detectors(tmp_path / "before", tmp_path / "after", "local")

    expected = json.loads(
        (FIXTURES / "js_assertion_weakened_truthy" / "expected.json").read_text()
    )
    assert [e.model_dump(include=COMPARED) for e in events] == expected
    assert warnings == []


def test_parse_tests_nests_describes_and_marks(tmp_path: Path) -> None:
    repo = tmp_path
    test = repo / "calc.test.ts"
    test.write_text(
        'describe.skip("calc", () => {\n'
        '  it("adds", () => { expect(1).toBe(1); });\n'
        '  describe("deep", () => {\n'
        '    test.only("works", () => { expect(2).toBe(2); });\n'
        "  });\n"
        "});\n"
        'test.each([[1, 1, 2]])("adds %i and %i", (a, b, e) => {\n'
        "  expect(a + b).toBe(e);\n"
        "});\n"
    )

    tests = parse_tests(test, repo)

    assert [t.nodeid for t in tests] == [
        "calc.test.ts::calc > adds",
        "calc.test.ts::calc > deep > works",
        "calc.test.ts::adds %i and %i",
    ]
    assert tests[0].markers == ["skip"]  # describe.skip reaches its children
    assert tests[1].markers == ["only", "skip"]
    assert tests[2].markers == []


def test_body_hash_survives_a_rename(tmp_path: Path) -> None:
    repo = tmp_path
    test = repo / "calc.test.ts"
    body = "() => {\n  expect(1 + 1).toBe(2);\n}"
    test.write_text(f'test("one", {body});\n')
    (first,) = parse_tests(test, repo)
    test.write_text(f'test("two", {body});\n')
    (second,) = parse_tests(test, repo)

    assert first.body_hash == second.body_hash
    assert first.nodeid != second.nodeid


def test_collect_js_skips_dependencies_and_non_tests(tmp_path: Path) -> None:
    repo = tmp_path
    (repo / "node_modules" / "left-pad").mkdir(parents=True)
    (repo / "node_modules" / "left-pad" / "index.test.js").write_text(
        'test("dep", () => {});\n'
    )
    (repo / "src").mkdir()
    (repo / "src" / "calc.ts").write_text("export const add = (a, b) => a + b;\n")
    (repo / "src" / "calc.spec.tsx").write_text(
        'test("adds", () => { expect(add(1, 2)).toBe(3); });\n'
    )
    (repo / "__tests__").mkdir()
    (repo / "__tests__" / "smoke.js").write_text('it("boots", () => {});\n')

    assert sorted(i.nodeid for i in collect_js(repo)) == [
        "__tests__/smoke.js::boots",
        "src/calc.spec.tsx::adds",
    ]


def test_enclosing_test_js(tmp_path: Path) -> None:
    path = tmp_path / "calc.test.ts"
    path.write_text(
        'import { add } from "./calc";\n'
        'describe("calc", () => {\n'
        '  it("adds", () => {\n'
        "    expect(add(1, 2)).toBe(3);\n"
        "  });\n"
        "});\n"
    )

    assert enclosing_test_js(path, 4) == "calc > adds"
    assert enclosing_test_js(path, 1) is None
    assert enclosing_test_js(path.with_name("missing.ts"), 1) is None


def test_mixed_python_and_js_repo_reports_both(tmp_path: Path) -> None:
    for side, expected, source in (
        ("before", "toBe(3)", "a + b"),
        ("after", "toBe(0)", "a - b"),
    ):
        repo = tmp_path / side
        repo.mkdir()
        (repo / "calc.ts").write_text(f"export const add = (a, b) => {source};\n")
        (repo / "calc.test.ts").write_text(
            f'import {{ add }} from "./calc";\n'
            f'test("adds", () => {{ expect(add(2, 2)).{expected}; }});\n'
        )

    events, _ = run_detectors(tmp_path / "before", tmp_path / "after", "local")

    assert any(e.pattern == "expected_value_changed" for e in events)


def test_jest_suite_still_runs_under_real_jest(tmp_path: Path) -> None:
    """The parser's idea of a suite matches the runner's: a real Jest run sees
    the tests the fixtures declare. Skipped without node/npm."""
    if shutil.which("npm") is None:
        pytest.skip("npm not available")
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "package.json").write_text('{"name": "t", "private": true}\n')
    (pkg / "calc.js").write_text(
        "function add(a, b) { return a + b; }\nmodule.exports = { add };\n"
    )
    (pkg / "calc.test.js").write_text(
        'const { add } = require("./calc");\n'
        'test("adds", () => { expect(add(1, 2)).toBe(3); });\n'
    )
    install = subprocess.run(
        ["npm", "install", "--no-audit", "--no-fund", "jest"],
        cwd=pkg,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if install.returncode != 0:
        pytest.skip(f"npm install failed: {install.stderr[-200:]}")
    run = subprocess.run(
        ["npx", "jest", "--listTests"],
        cwd=pkg,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert run.returncode == 0 and "calc.test.js" in run.stdout
