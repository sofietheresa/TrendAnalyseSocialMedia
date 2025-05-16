#!/usr/bin/env python3
"""
Hilfsskript zur Installation von NLTK und Download der benötigten NLTK-Daten
"""

import sys
import os
import logging
import subprocess
import importlib

# Konfiguriere logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nltk-setup")

def setup_nltk():
    """Installiere NLTK und lade die erforderlichen Daten herunter"""
    logger.info("=== NLTK SETUP SCRIPT ===")
    
    # 1. Überprüfe, ob NLTK installiert ist
    try:
        import nltk
        logger.info("NLTK is already installed")
    except ImportError:
        logger.info("NLTK is not installed, attempting to install...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'nltk'])
            logger.info("NLTK installed successfully")
            # Importiere nltk nach der Installation
            import nltk
        except Exception as e:
            logger.error(f"Failed to install NLTK: {e}")
            return False
    
    # 2. Lade benötigte NLTK-Daten herunter
    try:
        # Punkt-Tokenizer und POS-Tagger
        missing_packages = []
        
        try:
            nltk.data.find('tokenizers/punkt')
            logger.info("punkt tokenizer is already downloaded")
        except LookupError:
            missing_packages.append('punkt')
        
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
            logger.info("averaged_perceptron_tagger is already downloaded")
        except LookupError:
            missing_packages.append('averaged_perceptron_tagger')
        
        # Lade fehlende Pakete herunter
        if missing_packages:
            logger.info(f"Downloading missing NLTK packages: {', '.join(missing_packages)}")
            for package in missing_packages:
                nltk.download(package)
                logger.info(f"Downloaded {package} successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error downloading NLTK data: {e}")
        return False

if __name__ == "__main__":
    success = setup_nltk()
    if success:
        logger.info("NLTK setup completed successfully")
        sys.exit(0)
    else:
        logger.error("NLTK setup failed")
        sys.exit(1) 