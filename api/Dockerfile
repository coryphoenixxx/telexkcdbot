FROM python:3.9 as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* ./dist /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes



FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

COPY --from=requirements-stage /tmp/* /app/

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN pip install --no-cache-dir /app/telexkcdbot_api-1.0.0-py3-none-any.whl


COPY . /app
WORKDIR /app
