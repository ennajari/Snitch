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


def test_bin_takes_engine_and_mode_from_eval_variables(tmp_path: Path) -> None:
    # plugin eval runs pass only EVAL_* variables through to the plugin's hooks
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    payload = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git commit --no-verify -m x"},
    }
    env = {k: v for k, v in os.environ.items() if k != "SNITCH_ENGINE"}
    env |= {
        "EVAL_SNITCH_ENGINE": str(ROOT),
        "EVAL_SNITCH_MODE": "enforce",
        "CLAUDE_PLUGIN_OPTION_MODE": "warn",
        "CLAUDE_PLUGIN_DATA": str(tmp_path / "data"),
    }
    proc = subprocess.run(
        [str(PLUGIN / "bin" / "snitch"), "hook", "pre-tool"],
        input=json.dumps(payload),
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,  # the GitHub fallback would be slow, and would run pushed code
    )

    assert proc.returncode == 0, proc.stderr
    decision = json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"
