"""pytest plugin run inside the target repo's collection; dumps one record per test."""

import ast
import hashlib
import inspect
import json
import os
import textwrap
from pathlib import Path

import pytest

OUT_ENV = "SNITCH_INVENTORY_OUT"

type FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


def fingerprint(fn: FunctionNode) -> str:
    """Hash of the body only, so a rename or a new decorator keeps the same value."""
    return hashlib.sha1("".join(ast.dump(s) for s in fn.body).encode()).hexdigest()


def first_line(fn: FunctionNode) -> int:
    return min([fn.lineno, *(d.lineno for d in fn.decorator_list)])


# collection_finish, not modifyitems: session.items is final here (after -k / -m deselection).
def pytest_collection_finish(session: pytest.Session) -> None:
    records = []
    for item in session.items:
        file, line, name = item.location
        start = end = (line or 0) + 1
        body_hash = None
        try:
            lines, start = inspect.getsourcelines(item.function)  # type: ignore[attr-defined]
            fn = ast.parse(textwrap.dedent("".join(lines))).body[0]
            end = start + len(lines) - 1
            if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                body_hash = fingerprint(fn)
        except (AttributeError, OSError, TypeError, SyntaxError):
            pass  # not a plain Python function (doctest, generated test): no body to compare
        records.append(
            {
                "nodeid": item.nodeid,
                "file": Path(file).as_posix(),
                "line_start": start,
                "line_end": end,
                "name": getattr(item, "originalname", None) or name,
                "markers": sorted({m.name for m in item.iter_markers()}),
                "body_hash": body_hash,
            }
        )
    Path(os.environ[OUT_ENV]).write_text(json.dumps(records))
