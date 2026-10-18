import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
PLUGIN = ROOT / "plugin" / "snitch"

needs_claude = pytest.mark.skipif(
    shutil.which("claude") is None, reason="claude CLI not installed"
)


@needs_claude
@pytest.mark.parametrize(
    "target",
    [PLUGIN, ROOT / ".claude-plugin" / "marketplace.json"],
    ids=["plugin", "marketplace"],
)
def test_validate_strict(target: Path) -> None:
    proc = subprocess.run(
        ["claude", "plugin", "validate", "--strict", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_bin_runs_the_engine_cli() -> None:
    proc = subprocess.run(
        [str(PLUGIN / "bin" / "snitch"), "--help"],
        env={**os.environ, "SNITCH_ENGINE": str(ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert "diff" in proc.stdout
    assert "check" in proc.stdout
