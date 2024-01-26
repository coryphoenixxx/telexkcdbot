FROM python:3.11-alpine

ENV PIP_ROOT_USER_ACTION=ignore                 \
    PIP_DISABLE_PIP_VERSION_CHECK=on            \
    POETRY_VIRTUALENVS_IN_PROJECT=1             \
    POETRY_NO_INTERACTION=1                     \
    POETRY_VIRTUALENVS_OPTIONS_NO_PIP=1         \
    POETRY_VIRTUALENVS_OPTIONS_NO_SETUPTOOLS=1  \
    POETRY_VIRTUALENVS_PATH=.venv               \
    POETRY_CACHE_DIR=/tmp/poetry_cache          \
    PYTHONUNBUFFERED=1                          \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir poetry==1.7.1

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./


RUN poetry install --no-ansi -vvv --only api --no-root && rm -rf $POETRY_CACHE_DIR

COPY src/api /app/src/api
COPY src/shared /app/src/shared

RUN poetry install --only api

WORKDIR /app/src/api

CMD poetry run alembic upgrade head && poetry run gunicorn
