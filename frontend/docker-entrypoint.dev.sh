#!/bin/sh
set -e

echo "=========================="
echo "NextJS Development Server"
echo "=========================="
echo "Current directory: $(pwd)"
echo "Node version: $(node -v)"
echo "NPM version: $(npm -v)"

# Ensure path includes node_modules/.bin
export PATH="$PATH:/app/node_modules/.bin"

# Clean installation if node_modules is empty or package.json has changed
if [ ! -d "node_modules" ] || [ -z "$(ls -A node_modules 2>/dev/null)" ]; then
  echo "Installing dependencies..."
  # Remove any lock files to ensure clean install
  rm -f package-lock.json yarn.lock pnpm-lock.yaml
  
  # Install with development-friendly flags
  npm install --legacy-peer-deps --no-optional --no-package-lock
  
  echo "Dependencies installed successfully"
fi

# We'll skip cleaning .next directory since it's mounted as a volume

# Generate Prisma client
echo "Generating Prisma client..."
npx prisma generate

# Start the application
echo "Starting Next.js development server..."
exec "$@" 