FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files (build context should be project root)
COPY pyproject.toml .
COPY src/ ./src/

# Install only psycopg2-binary for the exchange server
RUN uv pip install --system psycopg2-binary

WORKDIR /app/src/exchange

ENTRYPOINT [ "python3", "server.py" ]
