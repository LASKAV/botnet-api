# Билдер: собираем зависимости
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Устанавливаем зависимости (без dev)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Копируем весь код + файлы
ADD . /app

# Повторно ставим проект уже с кодом
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# Финальный образ: минимальный, без uv
FROM python:3.12-slim-bookworm

# Устанавливаем FastAPI CLI (если используется fastapi-cli)
RUN pip install fastapi[all] fastapi-cli

WORKDIR /app

# Копируем все из builder
COPY --from=builder /app /app

# Установка переменной окружения для виртуального окружения
ENV PATH="/app/.venv/bin:$PATH"

COPY job-template.yaml /app/job-template.yaml

# Указываем команду запуска
CMD ["fastapi", "run", "/app/main.py", "--host", "0.0.0.0", "--port", "8000"]

