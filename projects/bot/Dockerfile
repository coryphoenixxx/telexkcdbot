FROM python:3.11.3-alpine as python
ENV PYTHONUNBUFFERED=1
WORKDIR /bot


FROM python as poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python -
COPY . ./
RUN poetry install --no-interaction --no-ansi -vvv


FROM python as runtime
ENV PATH="/bot/.venv/bin:$PATH"
COPY --from=poetry /bot /bot

CMD ["python", "-m", "src"]