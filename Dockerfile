# syntax=docker/dockerfile:1
# The identity service in a container: http://<host>:8000 (docs at /docs).
# It migrates the database (alembic upgrade head) before it starts, unless
# MIGRATE_ON_START=0. The JWT signing key is made in /data/keys on the first
# start: mount a volume on /data to keep it (or set JWT_PRIVATE_KEY).
#
#   docker build --network host -t balatro-identity .
#   docker run -p 8001:8000 --env-file .env -v identity-data:/data balatro-identity

FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project

FROM python:3.13-slim
RUN useradd --system --uid 10001 --no-create-home identity \
 && mkdir -p /data/keys && chown -R identity /data
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini docker-entrypoint.sh ./
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    JWT_PRIVATE_KEY_FILE=/data/keys/jwt_private.pem \
    MIGRATE_ON_START=1
USER identity
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
