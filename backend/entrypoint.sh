#!/bin/bash

# Seed reference data if needed
echo "Seeding reference data..."
python manage.py seed_reference_data --force

# Start the server
echo "Starting server..."
exec "$@" 