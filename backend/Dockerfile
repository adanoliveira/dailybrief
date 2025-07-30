FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV POETRY_VERSION=1.7.1

# Set work directory
WORKDIR /app

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn for production
RUN pip install --no-cache-dir gunicorn

# Create and activate a non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Copy project
COPY --chown=appuser:appuser . .

# Default to development server (can be overridden for production)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 