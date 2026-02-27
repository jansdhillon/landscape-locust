# landscape-locust

Load testing tool for Landscape Server that simulates traffic from Landscape Client instances.

## Setup

1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

2. Copy `.env.example` to `.env` and fill in your values:

```sh
cp .env.example .env
```

Key variables:

| Variable                                       | Description                                     |
| ---------------------------------------------- | ----------------------------------------------- |
| `LANDSCAPE_LOCUST_HOST`                        | URL of the Landscape server to target           |
| `LANDSCAPE_LOCUST_EMAIL`                       | Landscape account email (for `api` scenario)    |
| `LANDSCAPE_LOCUST_PASSWORD`                    | Landscape account password (for `api` scenario) |
| `LANDSCAPE_LOCUST_USERS`                       | Number of simulated users (default: 1000)       |
| `LANDSCAPE_LOCUST_SPAWN_RATE`                  | Users spawned per second (default: 50)          |
| `LANDSCAPE_LOCUST_WORKERS`                     | Number of Locust worker containers (default: 2) |
| `LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_HOST`     | Postgres host for the exchange server           |
| `LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_NAME`     | Postgres database name                          |
| `LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_USER`     | Postgres user                                   |
| `LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_PASSWORD` | Postgres password                               |
| `LANDSCAPE_LOCUST_NETWORK`                     | External Docker network name (local dev only)   |

## Usage

Each scenario has two variants: a regular one (external Landscape, DB reachable by hostname) and a `-local` one that joins the Docker network of a locally running Landscape Server dev setup.

### Ping traffic

```sh
make ping
make ping-local
```

### Message system traffic

```sh
make message
make message-local
```

### REST API traffic

```sh
make api
make api-local
```

### All scenarios

```sh
make run
make run-local
```
