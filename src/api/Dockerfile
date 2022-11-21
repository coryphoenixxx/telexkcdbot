FROM python:3.10.8-alpine as builder
COPY requirements.txt ./
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt



FROM python:3.10.8-alpine
WORKDIR /app
COPY . /app/api
COPY --from=builder /wheels /wheels
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
RUN pip install --no-cache /wheels/*

CMD ["python", "-m", "api"]
