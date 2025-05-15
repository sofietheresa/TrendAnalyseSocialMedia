#!/usr/bin/env python3
"""
Direkter Starter für Railway - Fixiert auf Port 8000
Railway versucht, den Dienst auf Port 8000 zu erreichen
"""

import sys
import os
import logging
import importlib
import subprocess

# Konfiguriere logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("railway-starter")

# Railway benötigt Port 8000
PORT = 8000

def check_dependencies():
    """Überprüfe, ob alle notwendigen Abhängigkeiten installiert sind"""
    required_modules = ["fastapi", "uvicorn", "sqlalchemy", "pandas", "pydantic"]
    missing_modules = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            logger.info(f"Modul {module} gefunden")
        except ImportError:
            logger.error(f"Modul {module} fehlt!")
            missing_modules.append(module)
    
    if missing_modules:
        logger.warning(f"Fehlende Module: {', '.join(missing_modules)}")
        logger.info("Versuche, fehlende Module zu installieren...")
        
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', '../requirements.txt'])
            logger.info("Abhängigkeiten wurden installiert")
        except Exception as e:
            logger.error(f"Fehler beim Installieren der Abhängigkeiten: {e}")
            return False
        
        # Überprüfe erneut
        for module in missing_modules:
            try:
                importlib.import_module(module)
                logger.info(f"Modul {module} wurde erfolgreich installiert")
            except ImportError:
                logger.error(f"Modul {module} konnte nicht installiert werden!")
                return False
    
    return True

def main():
    # Umgebungsdiagnostik
    logger.info("=== RAILWAY STARTER SCRIPT ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Railway environment detected")
    logger.info(f"PORT forced to {PORT}")
    
    # Überprüfe Abhängigkeiten
    if not check_dependencies():
        logger.error("Abhängigkeiten fehlen, beende Programm")
        sys.exit(1)
    
    # Setze PORT in Umgebungsvariable
    os.environ["PORT"] = str(PORT)
    
    # Starte Uvicorn direkt
    logger.info(f"Starting Uvicorn on 0.0.0.0:{PORT}")
    
    try:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="debug")
    except Exception as e:
        logger.error(f"Fehler beim Starten von Uvicorn: {e}")
        sys.exit(1)
    
if __name__ == "__main__":
    main() 