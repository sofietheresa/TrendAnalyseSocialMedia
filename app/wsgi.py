#!/usr/bin/env python3
"""WSGI entry point for Gunicorn"""

# The app variable is imported by Gunicorn
try:
    from main import app as application
    # Also provide 'app' for compatibility with both module imports
    app = application
except ImportError as e:
    import sys
    print(f"CRITICAL ERROR: Failed to import app from main.py: {e}", file=sys.stderr)
    raise

if __name__ == "__main__":
    application.run() 