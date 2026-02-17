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

.PHONY: docker-build db
db: docker-build
docker-build:
	docker build -t landscape-locust:latest .
	docker build -t landscape-locust/exchange-server:latest -f src/exchange/Dockerfile .

.PHONY: docker-build-exchange dbe
dbe: docker-build-exchange
docker-build-exchange:
	docker build -t landscape-locust/exchange-server:latest -f src/exchange/Dockerfile .

.PHONY: docker-build-locust dbl
dbl: docker-build-locust
docker-build-locust:
	docker build -t landscape-locust:latest .

.PHONY: docker-run-exchange dre
dre: docker-run-exchange
docker-run-exchange:
	docker run -p 9999:9999 landscape-locust/exchange-server:latest

.PHONY: compose-up up
up: compose-up
compose-up:
	docker-compose up -d

.PHONY: compose-down down
down: compose-down
compose-down:
	docker-compose down

.PHONY: compose-build cb
cb: compose-build
compose-build:
	docker-compose build

.PHONY: compose-logs logs
logs: compose-logs
compose-logs:
	docker-compose logs -f

.PHONY: compose-ping ping
ping: compose-ping
compose-ping:
	docker-compose up -d exchange-server locust-ping-master locust-ping-worker

.PHONY: compose-message message
message: compose-message
compose-message:
	docker-compose up -d exchange-server locust-message-master locust-message-worker

.PHONY: compose-api api docker-api
docker-api: compose-api
api: compose-api
compose-api:
	docker-compose up -d locust-api-master locust-api-worker
