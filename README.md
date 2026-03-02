# landscape-locust

Load testing tool for Landscape Server that simulates traffic from Landscape Client instances.

## Setup

1. Install [Docker](https://docs.docker.com/engine/install/ubuntu/).

2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

3. Copy `.env.example` to `.env` and fill in your values:

```sh
cp .env.example .env
```

Key variables:

| Variable                                       | Description                                                                  |
| ---------------------------------------------- | ---------------------------------------------------------------------------- |
| `LANDSCAPE_LOCUST_HOST`                        | URL of the Landscape server to target                                        |
| `LANDSCAPE_LOCUST_EMAIL`                       | Landscape account email (for `api` scenario, email/password login)           |
| `LANDSCAPE_LOCUST_PASSWORD`                    | Landscape account password (for `api` scenario, email/password login)        |
| `LANDSCAPE_LOCUST_ACCESS_KEY`                  | API access key (for `api` scenario, takes precedence over email/password)    |
| `LANDSCAPE_LOCUST_SECRET_KEY`                  | API secret key (for `api` scenario, used with `LANDSCAPE_LOCUST_ACCESS_KEY`) |
| `LANDSCAPE_LOCUST_USERS`                       | Number of simulated users (default: 1000)                                    |
| `LANDSCAPE_LOCUST_SPAWN_RATE`                  | Users spawned per second (default: 50)                                       |
| `LANDSCAPE_LOCUST_WORKERS`                     | Number of Locust worker containers (default: 2)                              |
| `LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_HOST`     | Postgres host for the exchange server                                        |
| `LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_NAME`     | Postgres database name                                                       |
| `LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_USER`     | Postgres user                                                                |
| `LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_PASSWORD` | Postgres password                                                            |

## Usage

### Ping traffic

```sh
make ping
```

### Message system traffic

```sh
make message
```

### REST API traffic

```sh
make api
```

### All scenarios

```sh
make run
```
