FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ARG USERNAME=$USERNAME
ARG UID=$UID
ARG GID=$GID

RUN groupadd --gid $GID $USERNAME \
    && useradd --uid $UID --gid $GID -m $USERNAME

USER $USERNAME

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

RUN --mount=type=cache,target=/opt/.cache/uv,uid=${UID},gid=${GID} \
    --mount=type=bind,source=/apps/backend/uv.lock,target=uv.lock \
    --mount=type=bind,source=/apps/backend/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

ADD apps/backend /app/backend

RUN --mount=type=cache,target=/opt/.cache/uv,uid=${UID},gid=${GID} \
    uv sync --frozen --no-dev

ENTRYPOINT []
