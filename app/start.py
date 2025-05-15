#!/usr/bin/env python3
"""Fallback-Starter für FastAPI"""

import os
import sys
import subprocess
import logging
import time

# Logging einrichten
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("starter")

# Wichtige Umgebungsinformationen loggen
logger.info("=== STARTER SCRIPT RUNNING ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Files in directory: {os.listdir()}")
logger.info(f"PORT from env: {os.environ.get('PORT', 'not set')}")

# Railway erwartet den Service auf Port 8000
PORT = 8000
logger.info(f"Using FIXED PORT {PORT} for Railway")

def run_uvicorn_directly():
    """Start the app directly with Uvicorn"""
    try:
        logger.info(f"Starting uvicorn directly on port {PORT}")
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(PORT)]
        logger.info(f"Running command: {' '.join(cmd)}")
        return subprocess.run(cmd, check=True)
    except Exception as e:
        logger.error(f"Error starting uvicorn directly: {e}")
        return None

def run_with_gunicorn():
    """Start the app with Gunicorn+Uvicorn worker"""
    try:
        logger.info("Starting with gunicorn and uvicorn worker")
        # Check if gunicorn is available
        try:
            import gunicorn
            logger.info(f"Gunicorn version: {gunicorn.__version__}")
        except ImportError:
            logger.error("Gunicorn not available")
            return None
            
        # Explizite Bindung an Port 8000 für Railway
        cmd = [
            sys.executable, "-m", "gunicorn", 
            "-k", "uvicorn.workers.UvicornWorker",
            "-b", f"0.0.0.0:{PORT}",
            "main:app"
        ]
        logger.info(f"Running command: {' '.join(cmd)}")
        return subprocess.run(cmd, check=True)
    except Exception as e:
        logger.error(f"Error starting with gunicorn: {e}")
        return None

if __name__ == "__main__":
    # Vor dem Start speziell für Railway anpassen
    os.environ["PORT"] = str(PORT)
    
    # Direkt mit Uvicorn starten (empfohlen)
    result = run_uvicorn_directly()
    
    # Wenn das fehlschlägt, versuche Gunicorn
    if result is None or result.returncode != 0:
        logger.warning("Direct uvicorn failed, trying gunicorn fallback")
        time.sleep(1)  # Kurze Pause
        run_with_gunicorn() 