FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app


RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev


ADD . /app


RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev



FROM python:3.12-slim-bookworm


RUN pip install fastapi[all] fastapi-cli

WORKDIR /app


COPY --from=builder /app /app


ENV PATH="/app/.venv/bin:$PATH"

COPY job-template.yaml /app/job-template.yaml


CMD ["fastapi", "run", "/app/main.py", "--host", "0.0.0.0", "--port", "8000"]

