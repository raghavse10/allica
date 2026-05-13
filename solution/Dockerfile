# syntax=docker/dockerfile:1.6
# ---------- builder ----------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only what we need to compile wheels (most are pure Python).
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ---------- runtime ----------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ALLICA_LOG_LEVEL=INFO \
    PORT=8000

# Run as a non-root user.
RUN groupadd -r allica && useradd -r -g allica allica

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

# Copy application code AFTER deps so source edits don't bust the cache.
COPY allica ./allica
COPY migrations ./migrations
COPY alembic.ini ./
# The companion data + docs folders live one level up in the dev repo; the
# image expects them mounted at /app/data and /app/docs in production. The
# bundled sample is provided here so the container is runnable standalone.
COPY ../data ./data
COPY ../docs ./docs

# Drop privileges and persist the SQLite default outside the image.
RUN mkdir -p /var/lib/allica && chown -R allica:allica /app /var/lib/allica
USER allica

ENV DATABASE_URL=sqlite:////var/lib/allica/allica.sqlite \
    ALLICA_DB_AUTO_MIGRATE=true

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["uvicorn", "allica.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
