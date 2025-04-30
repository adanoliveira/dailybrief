#!/bin/sh
set -e

# Log environment for debugging
echo "Running in NODE_ENV: $NODE_ENV"
echo "Current directory: $(pwd)"

# Regenerate Prisma client on startup
echo "Regenerating Prisma client..."
npx prisma generate

# Execute the main command
echo "Starting the application..."
exec "$@" 