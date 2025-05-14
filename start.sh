#!/bin/bash
export PORT="${PORT:-8000}"
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
