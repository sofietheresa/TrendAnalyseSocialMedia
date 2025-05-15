#!/usr/bin/env python3
"""ASGI entry point for Uvicorn/Gunicorn"""

# The app variable is imported by Gunicorn
try:
    from main import app
except ImportError as e:
    import sys
    print(f"CRITICAL ERROR: Failed to import app from main.py: {e}", file=sys.stderr)
    raise

if __name__ == "__main__":
    app.run() 