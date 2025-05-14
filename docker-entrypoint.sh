#!/bin/bash
set -e

# Start nginx in background
nginx -g 'daemon off;' &

# Start FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 