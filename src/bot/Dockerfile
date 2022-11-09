FROM python:3.10.8-alpine as builder
COPY requirements.txt ./
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt



FROM python:3.10.8-alpine
WORKDIR /bot
COPY . ./
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

CMD python __main__.py
