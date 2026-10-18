import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from pydantic import BaseModel

from engine.inventory._plugin import OUT_ENV


class InventoryError(RuntimeError):
    pass


class Item(BaseModel):
    nodeid: str
    file: str
    line_start: int
    line_end: int
    name: str
    markers: list[str]
    body_hash: str | None


def collect(repo: Path) -> list[Item]:
    """Collect the test inventory of `repo`. Runs the repo's conftest/import-time code."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "inventory.json"
        # shortcut: collects with Snitch's own interpreter, so the target repo's
        # dependencies must be importable here; run in the repo's venv when that breaks.
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
                f"--rootdir={repo}",
                "-p",
                "no:cacheprovider",
                "-p",
                "engine.inventory._plugin",
                # addopts can need plugins we lack (--cov) or deselect tests (-k);
                # the rules detector reports addopts changes instead.
                "-o",
                "addopts=",
            ],
            cwd=repo,
            check=False,
            env={
                **{k: v for k, v in os.environ.items() if k != "PYTEST_ADDOPTS"},
                OUT_ENV: str(out),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            capture_output=True,
            text=True,
        )
        # 5 = no tests collected, which is a valid (empty) inventory
        if proc.returncode not in (0, 5) or not out.exists():
            raise InventoryError(
                f"pytest collection failed in {repo} (exit {proc.returncode}):\n"
                f"{proc.stdout}{proc.stderr}"
            )
        return [Item(**record) for record in json.loads(out.read_text())]
