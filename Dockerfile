# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    ENVIRONMENT=production \
    SERVE_STATIC=true \
    DATA_DIR=/app/data \
    STATIC_DIR=/app/frontend/dist \
    HOST=0.0.0.0 \
    PORT=8001

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/ ./backend/
COPY content/ ./content/
COPY scripts/init-db.py ./scripts/init-db.py
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN pip install --no-cache-dir -e ./backend

RUN mkdir -p /app/data

VOLUME ["/app/data"]
EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/api/health')" || exit 1

CMD sh -c "python scripts/init-db.py && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"