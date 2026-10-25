import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pydantic import BaseModel

from engine.inventory import _plugin
from engine.inventory._plugin import OUT_ENV

PLUGIN = Path(_plugin.__file__)


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


PYTHON_ENV = "SNITCH_PYTHON"


def find_python(repo: Path) -> str | None:
    """The interpreter that can import the repo's tests: $SNITCH_PYTHON, else the repo's
    own .venv. None = Snitch's own. Only for a live repo the user set up, never for a
    tree an agent produced (it could plant a fake .venv/bin/python)."""
    if env := os.environ.get(PYTHON_ENV, "").strip():
        return env
    venv = repo / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return str(venv) if venv.is_file() else None


def _run_collection(
    repo: Path, python: str, out: Path
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as plugin_dir:
        # a standalone copy: the repo's interpreter has pytest but not Snitch
        shutil.copy(PLUGIN, Path(plugin_dir) / "snitch_inventory_plugin.py")
        path = os.pathsep.join(filter(None, [plugin_dir, os.environ.get("PYTHONPATH")]))
        return subprocess.run(
            [
                python,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
                f"--rootdir={repo}",
                "-p",
                "no:cacheprovider",
                "-p",
                "snitch_inventory_plugin",
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
                "PYTHONPATH": path,
            },
            capture_output=True,
            text=True,
        )


def collect(
    repo: Path, cache: Path | None = None, python: str | None = None
) -> list[Item]:
    """Collect the test inventory of `repo`. Runs the repo's conftest/import-time code,
    with `python` (see find_python) or else Snitch's own interpreter. With `cache`, a
    repo that never changes (a session baseline) is collected once."""
    if cache is not None and cache.is_file():
        return [Item(**record) for record in json.loads(cache.read_text())]
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "inventory.json"
        proc = _run_collection(repo, python or sys.executable, out)
        if python and "No module named pytest" in proc.stderr:
            # that environment has no pytest: Snitch's own is better than nothing
            proc = _run_collection(repo, sys.executable, out)
        # 5 = no tests collected, which is a valid (empty) inventory
        if proc.returncode not in (0, 5) or not out.exists():
            raise InventoryError(
                f"pytest collection failed in {repo} (exit {proc.returncode}):\n"
                f"{proc.stdout}{proc.stderr}"
            )
        if cache is not None:
            cache.write_text(out.read_text())
        return [Item(**record) for record in json.loads(out.read_text())]
