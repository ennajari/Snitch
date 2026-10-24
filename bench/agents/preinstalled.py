"""Benchmarked CLIs that ship preinstalled in the task images (pinned in the
Dockerfiles): installing them per trial took 13+ minutes on a slow network. Codex
and Claude Code already skip their install when the binary exists; Gemini CLI's
Harbor adapter always reinstalls through nvm, so this one checks first."""

from typing import Any

from harbor.agents.installed.gemini_cli import GeminiCli
from harbor.environments.base import BaseEnvironment

# Harbor requires a model name, but Gemini CLI's default is automatic routing (a
# flash-lite router picking flash or pro per request), which no --model value selects.
# `-m google/default` runs the CLI without --model, as a user would.
CLI_DEFAULT = "google/default"


class GeminiCliPreinstalled(GeminiCli):
    async def install(self, environment: BaseEnvironment) -> None:
        found = await environment.exec(command="command -v gemini")
        if found.return_code != 0:
            await super().install(environment)
            return
        await self.exec_as_agent(
            environment,
            command=(
                "mkdir -p ~/.gemini && "
                "cat > ~/.gemini/settings.json << 'SETTINGS'\n"
                '{\n  "experimental": {\n    "skills": true\n  }\n}\n'
                "SETTINGS"
            ),
        )

    async def exec_as_agent(
        self, environment: BaseEnvironment, command: str, *args: Any, **kwargs: Any
    ) -> Any:
        if self.model_name == CLI_DEFAULT:
            command = command.replace("--model=default ", "")
        return await super().exec_as_agent(environment, command, *args, **kwargs)
