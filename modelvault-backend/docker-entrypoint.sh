#!/bin/sh
set -e

echo "Starting ModelVault Production Container Entrypoint..."

# Wait for Database readiness if POSTGRES_SERVER is configured
if [ -n "$POSTGRES_SERVER" ]; then
    echo "Checking database connectivity at $POSTGRES_SERVER:$POSTGRES_PORT..."
    python -c "
import socket
import time
import os

host = os.environ.get('POSTGRES_SERVER', 'localhost')
port = int(os.environ.get('POSTGRES_PORT', 5432))
for _ in range(30):
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        print('Database connection established!')
        break
    except Exception:
        time.sleep(1)
"
fi

# Run Database Migrations
echo "Executing Alembic database migrations..."
alembic upgrade head || echo "Database migrations skipped or up to date."

# Seed & Ingest Organizer Data if configured
if [ "$AUTO_INGEST_ON_STARTUP" = "true" ]; then
    echo "Executing automated data ingestion and ML model bootstrap..."
    python -m app.ingestion.load_data || echo "Ingestion completed or skipped."
fi

# Start Production ASGI Server
echo "Starting Uvicorn ASGI production server on port 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
