# botnet-api

Backend HTTP API built with FastAPI. It stores its state in PostgreSQL and can optionally launch worker jobs in a Kubernetes cluster.

## Tech stack

- Python 3.12+, managed with [uv](https://docs.astral.sh/uv/)
- FastAPI (async) and SQLModel on top of asyncpg
- Alembic for database migrations
- kubernetes-asyncio for launching jobs from `job-template.yaml` (optional)
- Docker (multi-stage build)

## Project layout

```
main.py          FastAPI app and router registration
settings.py      Configuration loaded from environment / .env
database.py      Async DB session setup
models/          SQLModel table definitions
modules/         API routers, one per resource
migrations/      Alembic migrations
job-template.yaml  Kubernetes Job template
```

## Configuration

Settings are read from environment variables or a `.env` file.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | yes | PostgreSQL DSN |
| `ENABLE_KUBE` | yes | `true` to enable the Kubernetes jobs router |
| `KUBE_CONFIG_PATH` | no | Path to a kubeconfig; if unset, in-cluster config is used |
| `KUBE_CONTEXT` | no | Kubeconfig context to use |
| `KUBE_NAMESPACE` | no | Namespace in which jobs are created |

## Running locally

```bash
uv sync
alembic upgrade head
fastapi dev main.py
```

Interactive API docs are served at `/docs`.

## Docker

```bash
docker build -t botnet-api .
docker run --env-file .env -p 8000:8000 botnet-api
```

## How to deal with database

### Run migrations to the latest version

```bash
alembic upgrade head
```

### View migration SQL code (offline mode)

```bash
alembic upgrade head --sql
```

### Generate new migration

```bash
alembic revision --autogenerate -m "message"
```

**Be sure to check if the correct operations have been generated!**
