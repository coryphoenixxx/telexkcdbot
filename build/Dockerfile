FROM python:3.12-slim AS exchange-poetry

ENV PYTHONUNBUFFERED=1
WORKDIR /apps
RUN pip3 install --no-cache-dir poetry


FROM exchange-poetry AS exchange-base
COPY apps/backend/pyproject.toml pyproject.toml
RUN poetry install --no-root --only main


FROM exchange-base AS exchange-main
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
COPY apps/backend /app/backend
WORKDIR /app/backend
RUN poetry install --only main
