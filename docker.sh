#!/bin/bash

# Helper script for Docker operations
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Usage information
show_usage() {
  echo -e "${YELLOW}DailyBrief Docker Helper${NC}"
  echo ""
  echo "Usage: ./docker.sh [command]"
  echo ""
  echo "Commands:"
  echo "  up        Start all services"
  echo "  down      Stop all services"
  echo "  build     Rebuild all services"
  echo "  restart   Restart all services"
  echo "  logs      Show logs from all services"
  echo "  django    Run Django management command"
  echo "  migrate   Run database migrations"
  echo "  shell     Open Django shell"
  echo "  npm       Run npm command in frontend"
  echo "  clean     Remove all containers and volumes"
  echo "  help      Show this help message"
}

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
  if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    alias docker-compose="docker compose"
  else
    echo -e "${RED}Docker Compose is not installed.${NC}"
    exit 1
  fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
  echo -e "${YELLOW}Creating .env file from .env.example${NC}"
  cp .env.example .env
fi

# Command handlers
case "$1" in
  up)
    echo -e "${GREEN}Starting all services...${NC}"
    docker-compose up -d
    echo -e "${GREEN}Services are running!${NC}"
    echo "- Backend: http://localhost:8000"
    echo "- Frontend: http://localhost:3000"
    ;;
  down)
    echo -e "${GREEN}Stopping all services...${NC}"
    docker-compose down
    ;;
  build)
    echo -e "${GREEN}Rebuilding all services...${NC}"
    docker-compose build
    ;;
  restart)
    echo -e "${GREEN}Restarting all services...${NC}"
    docker-compose restart
    ;;
  logs)
    echo -e "${GREEN}Showing logs...${NC}"
    docker-compose logs -f
    ;;
  django)
    if [ -z "$2" ]; then
      echo -e "${RED}Please specify a Django command.${NC}"
      echo "Example: ./docker.sh django createsuperuser"
      exit 1
    fi
    shift
    echo -e "${GREEN}Running Django command: $@${NC}"
    docker-compose exec backend python manage.py "$@"
    ;;
  migrate)
    echo -e "${GREEN}Running migrations...${NC}"
    docker-compose exec backend python manage.py migrate
    ;;
  shell)
    echo -e "${GREEN}Opening Django shell...${NC}"
    docker-compose exec backend python manage.py shell
    ;;
  npm)
    if [ -z "$2" ]; then
      echo -e "${RED}Please specify an npm command.${NC}"
      echo "Example: ./docker.sh npm install axios"
      exit 1
    fi
    shift
    echo -e "${GREEN}Running npm command: $@${NC}"
    docker-compose exec frontend npm "$@"
    ;;
  clean)
    echo -e "${YELLOW}Warning: This will remove all containers and volumes.${NC}"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${GREEN}Removing all containers and volumes...${NC}"
      docker-compose down -v
    fi
    ;;
  help | *)
    show_usage
    ;;
esac 