FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

RUN --mount=type=cache,target=.cache/uv \
    --mount=type=bind,source=/apps/backend/uv.lock,target=uv.lock \
    --mount=type=bind,source=/apps/backend/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

ADD apps/backend /app/backend

RUN --mount=type=cache,target=.cache/uv \
    uv sync --frozen --no-dev

ENTRYPOINT []
