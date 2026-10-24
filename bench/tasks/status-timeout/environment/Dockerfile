FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git curl nodejs npm procps \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/
RUN uv pip install --system pytest==8.4.1
# Claude Code preinstalled (pinned): its ~13-minute download would otherwise repeat in
# every trial; Harbor skips its own install when `claude` is on PATH. Other agents
# install themselves as usual.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash -s -- 2.1.310 \
    && ln -s /root/.local/bin/claude /usr/local/bin/claude
WORKDIR /app
COPY repo/ /app/
RUN git init -q && git add -A \
    && git -c user.name=dev -c user.email=dev@example.com commit -qm init
