#!/bin/bash
set -e

# Run migrations
echo "Running database migrations..."
# In a real setup, we might wait for the DB here
# wait-for-it db:5432 -t 60

alembic upgrade head

# Start server
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000