import json
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
    # added after the first build: fails if bin/snitch runs a stale copy of the engine
    assert "hook" in proc.stdout


def test_mode_is_a_user_config_picker_defaulting_to_warn() -> None:
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())

    mode = manifest["userConfig"]["mode"]

    assert mode["type"] == "string"
    assert mode["options"] == ["observe", "warn", "enforce"]
    assert mode["default"] == "warn"
