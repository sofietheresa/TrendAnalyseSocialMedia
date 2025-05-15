#!/usr/bin/env python3
"""
Direkter Starter für Railway - Fixiert auf Port 8000
Railway versucht, den Dienst auf Port 8000 zu erreichen
"""

import sys
import os
import logging
import uvicorn

# Konfiguriere logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("railway-starter")

# Railway benötigt Port 8000
PORT = 8000

def main():
    # Umgebungsdiagnostik
    logger.info("=== RAILWAY STARTER SCRIPT ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Railway environment detected")
    logger.info(f"PORT forced to {PORT}")
    
    # Setze PORT in Umgebungsvariable
    os.environ["PORT"] = str(PORT)
    
    # Starte Uvicorn direkt
    logger.info(f"Starting Uvicorn on 0.0.0.0:{PORT}")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="debug")
    
if __name__ == "__main__":
    main() 