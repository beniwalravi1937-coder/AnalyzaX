# ==============================================================================
# AnalyzaX Backend — Production Multi-Stage Dockerfile
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependency Builder
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Production Runtime Image (Non-Root User)
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS production

WORKDIR /app

# Install minimal runtime libraries (libpq for Postgres) and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user and group
RUN groupadd -g 10001 analyzax && \
    useradd -u 10001 -g analyzax -s /bin/bash -m analyzax

# Copy installed Python dependencies from builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY . /app/backend

# Create required persistent data directories with appropriate permissions
RUN mkdir -p /app/data/uploads /app/data/processed /app/data/profiles /app/data/quality \
             /app/data/exports /app/data/jobs /app/data/migrations /app/data/temp \
    && chown -R analyzax:analyzax /app

# Switch to non-root user
USER analyzax:analyzax

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    DATA_STORAGE_ROOT=/app/data

EXPOSE 8000

# Docker healthcheck querying the lightweight liveness endpoint
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
