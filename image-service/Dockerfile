FROM tecktron/python-bjoern:python-3.11-slim AS python

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app


FROM python AS poetry

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())'\
    | python -

COPY . ./
RUN poetry install --no-interaction --no-ansi -vvv

FROM python AS runtime

ENV PATH="/app/.venv/bin:$PATH"
COPY --from=poetry /app /app

CMD ["python", "-m", "src"]
