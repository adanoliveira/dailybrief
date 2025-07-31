FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies and build tools in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Copy requirements first for better caching
COPY requirements-staging.txt requirements.txt

# Install Python dependencies with cleanup
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf ~/.cache/pip

# Create and activate a non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Copy project
COPY --chown=appuser:appuser . .

# Production server (Railway will override with its own start command)
CMD ["gunicorn", "dailybrief.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "gevent"] 