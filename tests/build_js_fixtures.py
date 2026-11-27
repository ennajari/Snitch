"""Build tests/fixtures_js/*: before/after repo pairs for the JS detectors."""

import shutil
from pathlib import Path

ROOT = Path(__file__).parent / "fixtures_js"

CALC_TS = "export function add(a: number, b: number): number {\n  return a + b;\n}\n"
CALC_BUGGY = "export function add(a: number, b: number): number {\n  return a - b;\n}\n"
DB_TS = "export function query(sql: string): string[] {\n  return [sql];\n}\n"

# name -> (before files, after files); each maps relpath -> content
FIXTURES: dict[str, tuple[dict[str, str], dict[str, str]]] = {}

# --- inventory -------------------------------------------------------------
TWO_TESTS = (
    'import { add } from "./calc";\n'
    'test("adds", () => { expect(add(1, 2)).toBe(3); });\n'
    'test("subtracts", () => { expect(add(2, 1)).toBe(3); });\n'
)
FIXTURES["js_test_deleted"] = (
    {"calc.ts": CALC_TS, "calc.test.ts": TWO_TESTS},
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": 'import { add } from "./calc";\n'
        'test("adds", () => { expect(add(1, 2)).toBe(3); });\n',
    },
)
FIXTURES["js_test_skipped"] = (
    {"calc.ts": CALC_TS, "calc.test.ts": TWO_TESTS.replace("subtracts", "subtracts")},
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": TWO_TESTS.replace('test("subtracts"', 'test.skip("subtracts"'),
    },
)
FIXTURES["js_test_skipped_xit"] = (
    {"calc.ts": CALC_TS, "calc.test.ts": TWO_TESTS},
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": TWO_TESTS.replace('test("subtracts"', 'xit("subtracts"'),
    },
)
FIXTURES["js_test_pending"] = (
    {"calc.ts": CALC_TS, "calc.test.ts": TWO_TESTS},
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": TWO_TESTS.replace(
            'test("subtracts", () => { expect(add(2, 1)).toBe(3); });',
            'test("subtracts");',
        ),
    },
)
FIXTURES["js_test_focused"] = (
    {"calc.ts": CALC_TS, "calc.test.ts": TWO_TESTS},
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": TWO_TESTS.replace('test("adds"', 'test.only("adds"'),
    },
)
FIXTURES["js_legit_test_renamed"] = (
    {"calc.ts": CALC_TS, "calc.test.ts": TWO_TESTS},
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": TWO_TESTS.replace('test("subtracts"', 'test("adds positive"'),
    },
)
FIXTURES["js_legit_skip_unchanged"] = (
    {"calc.ts": CALC_TS, "calc.test.ts": TWO_TESTS},
    {"calc.ts": CALC_TS, "calc.test.ts": TWO_TESTS},
)

# --- assertion diff ----------------------------------------------------------
BASE = 'import { add } from "./calc";\n'


def suite(body: str) -> str:
    return BASE + body


FIXTURES["js_assertion_weakened_truthy"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_BUGGY,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBeTruthy();\n});\n'
        ),
    },
)
FIXTURES["js_assertion_weakened_bound"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("small error", () => {\n'
            "  const err = Math.abs(add(1, 2) - 3);\n"
            "  expect(err).toBeLessThan(0.01);\n"
            "});\n"
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("small error", () => {\n'
            "  const err = Math.abs(add(1, 2) - 3);\n"
            "  expect(err).toBeLessThan(1);\n"
            "});\n"
        ),
    },
)
FIXTURES["js_legit_bound_tightened"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite('test("t", () => {\n  expect(x).toBeLessThan(1);\n});\n'),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("t", () => {\n  expect(x).toBeLessThan(0.01);\n});\n'
        ),
    },
)
FIXTURES["js_assertion_weakened_negated"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).not.toBe(3);\n});\n'
        ),
    },
)
FIXTURES["js_assertion_weakened_throw"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("throws", () => {\n'
            '  expect(() => add(NaN, 1)).toThrow("invalid input");\n'
            "});\n"
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("throws", () => {\n  expect(() => add(NaN, 1)).toThrow();\n});\n'
        ),
    },
)
FIXTURES["js_assertion_weakened_identity"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("same object", () => {\n  expect(cache.get(1)).toBe(cached);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("same object", () => {\n  expect(cache.get(1)).toEqual(cached);\n});\n'
        ),
    },
)
FIXTURES["js_assertion_removed"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n'
            "  expect(add(1, 2)).toBe(3);\n"
            "  expect(add(-1, 1)).toBe(0);\n"
            "});\n"
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n'
        ),
    },
)
FIXTURES["js_legit_assert_added"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n'
            "  expect(add(1, 2)).toBe(3);\n"
            "  expect(add(-1, 1)).toBe(0);\n"
            "});\n"
        ),
    },
)
FIXTURES["js_legit_assertion_strengthened"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBeTruthy();\n});\n'
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n'
        ),
    },
)
FIXTURES["js_expected_value_changed"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(2, 2)).toBe(4);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_BUGGY,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(2, 2)).toBe(0);\n});\n'
        ),
    },
)
FIXTURES["js_legit_expected_updated"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(2, 2)).toBe(4);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  // the spec now says integers round down\n'
            "  expect(add(2, 2)).toBe(4);\n"
            "  expect(add(0, 0)).toBe(0);\n"
            "});\n"
        ),
    },
)
FIXTURES["js_assertion_rewritten"] = (
    {
        "calc.ts": "export function hours(s: number): number {\n  return s / 3600;\n}\n",
        "calc.test.ts": suite(
            'test("one hour", () => {\n  expect(hours(3600)).toBe(1);\n});\n'
        ),
    },
    {
        "calc.ts": "export function hours(s: number): number {\n  return s / 60;\n}\n",
        "calc.test.ts": suite(
            'test("one hour", () => {\n  expect(hours(3600) * 60).toBe(1);\n});\n'
        ),
    },
)
FIXTURES["js_assertion_guarded"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n'
            "  if (process.env.CI_STRICT) {\n"
            "    expect(add(1, 2)).toBe(3);\n"
            "  }\n"
            "});\n"
        ),
    },
)
FIXTURES["js_legit_refactor_same_asserts"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1,2)).toBe(3);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n'
            "  // formatting only\n"
            "  expect(add(1, 2)).toBe(3);\n"
            "});\n"
        ),
    },
)
FIXTURES["js_test_scope_reduced"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("many cases", () => {\n'
            "  for (let i = 0; i < 20000; i++) {\n"
            "    expect(add(i, 0)).toBe(i);\n"
            "  }\n"
            "});\n"
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("many cases", () => {\n'
            "  for (let i = 0; i < 100; i++) {\n"
            "    expect(add(i, 0)).toBe(i);\n"
            "  }\n"
            "});\n"
        ),
    },
)
FIXTURES["js_mock_code_under_test"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": 'import { vi } from "vitest";\n'
        'import { add } from "./calc";\n'
        'vi.mock("./calc");\n'
        'test("adds", () => {\n'
        "  vi.mocked(add).mockReturnValue(3);\n"
        "  expect(add(1, 2)).toBe(3);\n"
        "});\n",
    },
)
FIXTURES["js_legit_mock_dependency"] = (
    {
        "calc.ts": CALC_TS,
        "db.ts": DB_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n'
        ),
    },
    {
        "calc.ts": CALC_TS,
        "db.ts": DB_TS,
        "calc.test.ts": 'import { vi } from "vitest";\n'
        'import { add } from "./calc";\n'
        'vi.mock("./db");\n'
        'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n',
    },
)
FIXTURES["js_legit_test_split"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n'
            "  expect(add(1, 2)).toBe(3);\n"
            "  expect(add(-1, 1)).toBe(0);\n"
            "});\n"
        ),
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": suite(
            'test("adds", () => {\n  expect(add(1, 2)).toBe(3);\n});\n'
            'test("adds negatives", () => {\n  expect(add(-1, 1)).toBe(0);\n});\n'
        ),
    },
)
FIXTURES["js_assertion_weakened_nested"] = (
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": BASE
        + 'describe("calc", () => {\n'
        + '  describe("add", () => {\n'
        + '    it("adds", () => {\n      expect(add(1, 2)).toBe(3);\n    });\n'
        + "  });\n"
        + "});\n",
    },
    {
        "calc.ts": CALC_TS,
        "calc.test.ts": BASE
        + 'describe("calc", () => {\n'
        + '  describe("add", () => {\n'
        + '    it("adds", () => {\n      expect(add(1, 2)).toBeDefined();\n    });\n'
        + "  });\n"
        + "});\n",
    },
)

# --- rules -------------------------------------------------------------------
PKG = '{\n  "name": "app",\n  "scripts": {\n    "test": "jest"\n  }\n}\n'
FIXTURES["js_test_script_weakened"] = (
    {"package.json": PKG, "calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
    {
        "package.json": PKG.replace('"test": "jest"', '"test": "echo done"'),
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
)
FIXTURES["js_pass_with_no_tests_script"] = (
    {"package.json": PKG, "calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
    {
        "package.json": PKG.replace(
            '"test": "jest"', '"test": "jest --passWithNoTests"'
        ),
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
)
FIXTURES["js_script_or_true"] = (
    {
        "package.json": PKG.replace("jest", "vitest run"),
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
    {
        "package.json": PKG.replace('"test": "jest"', '"test": "vitest run || true"'),
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
)
JEST_JSON = (
    '{\n  "coverageThreshold": {\n    "global": {\n'
    '      "statements": 80,\n      "branches": 80\n    }\n  }\n}\n'
)
FIXTURES["js_coverage_threshold_lowered"] = (
    {"jest.config.json": JEST_JSON, "calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
    {
        "jest.config.json": JEST_JSON.replace('"statements": 80', '"statements": 50'),
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
)
PKG_JEST = (
    '{\n  "name": "app",\n  "scripts": {\n    "test": "jest"\n  },\n'
    '  "jest": {\n    "coverageThreshold": {\n      "global": {\n        "lines": 90\n'
    "      }\n    }\n  }\n}\n"
)
FIXTURES["js_coverage_threshold_removed"] = (
    {"package.json": PKG_JEST, "calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
    {"package.json": PKG, "calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
)
JEST_JS = 'module.exports = {\n  testEnvironment: "node",\n};\n'
FIXTURES["js_config_pass_with_no_tests"] = (
    {"jest.config.js": JEST_JS, "calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
    {
        "jest.config.js": JEST_JS.replace("};", "  passWithNoTests: true,\n};"),
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
)
FIXTURES["js_test_paths_ignored"] = (
    {"jest.config.js": JEST_JS, "calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
    {
        "jest.config.js": JEST_JS.replace(
            "};", '  testPathIgnorePatterns: ["/node_modules/", "calc.test.ts"],\n};'
        ),
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
)
FIXTURES["js_legit_config_created"] = (
    {"calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
    {
        "vitest.config.ts": 'import { defineConfig } from "vitest/config";\n'
        "export default defineConfig({\n"
        "  test: { passWithNoTests: true },\n"
        "});\n",
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
)
FIXTURES["js_legit_coverage_raised"] = (
    {"jest.config.json": JEST_JSON, "calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
    {
        "jest.config.json": JEST_JSON.replace('"statements": 80', '"statements": 95'),
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
)
FIXTURES["js_legit_script_verbose"] = (
    {"package.json": PKG, "calc.test.ts": TWO_TESTS, "calc.ts": CALC_TS},
    {
        "package.json": PKG.replace('"test": "jest"', '"test": "jest --verbose"'),
        "calc.test.ts": TWO_TESTS,
        "calc.ts": CALC_TS,
    },
)


def main() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    for name, (before, after) in FIXTURES.items():
        for side, files in (("before", before), ("after", after)):
            base = ROOT / name / side
            base.mkdir(parents=True)
            for rel, content in files.items():
                path = base / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
    print(f"{len(FIXTURES)} fixtures written to {ROOT}")


if __name__ == "__main__":
    main()
