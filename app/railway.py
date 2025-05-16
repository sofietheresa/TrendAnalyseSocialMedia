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
    required_modules = ["fastapi", "uvicorn", "sqlalchemy", "pandas", "pydantic", "nltk"]
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
    
    # Stelle sicher, dass NLTK-Daten vorhanden sind
    try:
        logger.info("Checking NLTK data...")
        import nltk
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('taggers/averaged_perceptron_tagger')
            logger.info("NLTK data already exists")
        except LookupError:
            logger.info("Downloading NLTK data...")
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
            logger.info("NLTK data downloaded successfully")
    except Exception as e:
        logger.error(f"Error with NLTK data: {e}")
        # Nicht beenden, da es möglicherweise noch funktionieren könnte
    
    # Setze PORT in Umgebungsvariable
    os.environ["PORT"] = str(PORT)
    
    # Starte Uvicorn direkt
    logger.info(f"Starting Uvicorn on 0.0.0.0:{PORT}")
    
    try:
        import uvicorn
        logger.info(f"Trying to run Uvicorn with main:app in directory: {os.getcwd()}")
        # Die app-Variable sollte in main.py definiert sein
        if os.path.exists("main.py"):
            uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
        else:
            # Falls main.py nicht im aktuellen Verzeichnis ist, versuche es mit relativem Pfad
            logger.info("main.py not found in current directory, trying alternative paths")
            # Wenn wir uns im app-Verzeichnis befinden und main.py hier ist
            uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
    except Exception as e:
        logger.error(f"Fehler beim Starten von Uvicorn: {e}")
        sys.exit(1)
    
if __name__ == "__main__":
    main() 