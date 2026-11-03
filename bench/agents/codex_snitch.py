"""Harbor agent for the bench's with_snitch arm: Codex CLI with the Snitch plugin.

    PYTHONPATH=. harbor run -p bench/tasks -a bench.agents.codex_snitch:CodexWithSnitch \
        -m openai/gpt-6.1-sol --ae SNITCH_MODE=warn ...

The plugin is cloned from GitHub into the container, so push before a run. Codex
skips hooks nobody has trusted, and an unattended run cannot trust them in `/hooks`,
so this passes --dangerously-bypass-hook-trust (the hook source is this repo).
"""

from typing import Any

from harbor.agents.installed.codex import Codex
from harbor.environments.base import BaseEnvironment

PLUGIN_REPO = "https://github.com/ennajari/snitch"
CHECKOUT = "/opt/snitch"


class CodexWithSnitch(Codex):
    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        await self.exec_as_root(
            environment,
            # retried like the Claude Code arm: DNS lookups fail now and then
            command=(
                "for attempt in 1 2 3; do"
                f" rm -rf {CHECKOUT} && git clone -q --depth 1 {PLUGIN_REPO} {CHECKOUT}"
                " && break; sleep $((attempt * 10)); done"
                f" && test -d {CHECKOUT}/plugin/snitch/.codex-plugin"
                f" && chmod -R a+rX {CHECKOUT}"
            ),
        )
        home = self._REMOTE_CODEX_HOME.as_posix()
        await self.exec_as_agent(
            environment,
            # run() reuses this CODEX_HOME; the uvx warm-up keeps the MCP server's
            # first start inside Codex's connect timeout
            command=(
                f"mkdir -p {home} && export CODEX_HOME={home}"
                f" && git config --global --add safe.directory {CHECKOUT}"
                f" && codex plugin marketplace add {CHECKOUT}"
                " && codex plugin add snitch@snitch"
                " && for attempt in 1 2 3; do"
                f" {CHECKOUT}/plugin/snitch/bin/snitch --help >/dev/null && break;"
                " sleep $((attempt * 10)); done"
            ),
        )

    def _build_effective_config(
        self, openai_base_url: str | None = None
    ) -> dict[str, Any]:
        # run() rewrites config.toml, which is where `plugin add` enabled the plugin
        config = super()._build_effective_config(openai_base_url)
        config.setdefault("marketplaces", {})["snitch"] = {
            "source_type": "local",
            "source": CHECKOUT,
        }
        config.setdefault("plugins", {})["snitch@snitch"] = {"enabled": True}
        return config

    def build_cli_flags(self) -> str:
        return f"{super().build_cli_flags()} --dangerously-bypass-hook-trust".strip()
