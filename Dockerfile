FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

ENV PATH="/app/.venv/bin:$PATH"

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8080
