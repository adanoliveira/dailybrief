#!/bin/bash

# Load environment variables from .env file
set -a
if [ -f .env ]; then
  source .env
fi
set +a

# Set default Django settings module
export DJANGO_SETTINGS_MODULE=dailybrief.settings

# Change to project directory
cd "${PROJECT_DIR:-./backend}"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Define functions for different Celery commands
start_worker() {
  echo "Starting Celery worker..."
  celery -A dailybrief worker --loglevel=info
}

start_beat() {
  echo "Starting Celery beat scheduler..."
  celery -A dailybrief beat --loglevel=info
}

start_flower() {
  echo "Starting Flower monitoring tool..."
  celery -A dailybrief flower
}

# Handle command line arguments
case "$1" in
  worker)
    start_worker
    ;;
  beat)
    start_beat
    ;;
  flower)
    start_flower
    ;;
  all)
    # Start all in background except for the last one
    celery -A dailybrief beat --loglevel=info --detach
    celery -A dailybrief flower --detach
    start_worker  # Keep the worker in foreground
    ;;
  *)
    echo "Usage: $0 {worker|beat|flower|all}"
    exit 1
    ;;
esac

exit 0 