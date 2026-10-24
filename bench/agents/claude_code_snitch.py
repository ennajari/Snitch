"""Harbor agent for the bench's with_snitch arm: Claude Code with the Snitch plugin.

    PYTHONPATH=. harbor run -p bench/tasks \
        -a bench.agents.claude_code_snitch:ClaudeCodeWithSnitch \
        --ae EVAL_SNITCH_MODE=enforce ...

The plugin is cloned from GitHub into the container, so push before a run. Its hooks
install the engine with uvx on first use (the task images ship uv). Mode comes from
EVAL_SNITCH_MODE (bin/snitch), default warn.
"""

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.environments.base import BaseEnvironment

PLUGIN_REPO = "https://github.com/ennajari/snitch"
CHECKOUT = "/opt/snitch"


class ClaudeCodeWithSnitch(ClaudeCode):
    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        await self.exec_as_root(
            environment,
            command=(
                f"rm -rf {CHECKOUT} && git clone -q --depth 1 {PLUGIN_REPO} {CHECKOUT}"
                f" && chmod -R a+rX {CHECKOUT}"
            ),
        )

    def build_cli_flags(self) -> str:
        flags = super().build_cli_flags()
        return f"{flags} --plugin-dir {CHECKOUT}/plugin/snitch".strip()
