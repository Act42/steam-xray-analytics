# Production Dockerfile for SteamXRay v2.0 (FastAPI + Uvicorn)
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging for cloud stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# 1. Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 2. Copy application source code and static frontend assets
COPY src/ ./src/
COPY static/ ./static/
COPY tests/ ./tests/
COPY README.md ./

# 3. Create a non-root user for container security best practices
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Bind to 0.0.0.0 and dynamically use Render's $PORT environment variable
CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
