FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml .
COPY src/ ./src/

RUN uv venv --clear && uv pip install -e .

ENV PATH="/app/.venv/bin:$PATH"

CMD ["locust"]
