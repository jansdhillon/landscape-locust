.PHONY: build
build:
	uv venv --clear
	uv pip install -e .[dev]

.PHONY: check
check:
	uv run ruff check
	uv run ruff format --check

.PHONY: lint
lint:
	uv run ruff check --fix
	uv run ruff format

.PHONY: watch
up:
	docker compose up -d --build

.PHONY: up
up:
	docker compose up -d --build

.PHONY: down
down:
	docker compose down

.PHONY: logs
logs:
	docker compose logs -f

.PHONY: ping
ping:
	docker compose up -d --build exchange-server locust-ping-master locust-ping-worker

.PHONY: message
message:
	docker compose up -d --build exchange-server locust-message-master locust-message-worker

.PHONY: api
api:
	docker compose up -d --build exchange-server locust-api-master locust-api-worker
