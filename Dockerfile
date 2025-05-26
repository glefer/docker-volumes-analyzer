FROM python:3.13-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.2

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /build

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-interaction --no-ansi --no-root
COPY . .

RUN poetry build

FROM python:3.13-slim AS runtime

WORKDIR /app
ENV PYTHONUNBUFFERED=1

ARG APP_VERSION='undefined'
ENV APP_VERSION=${APP_VERSION}

COPY --from=builder /build/dist/*.whl ./dist/

RUN pip install ./dist/*.whl

CMD ["start"]
