import logging
from pathlib import Path
from datetime import datetime

# Konfiguration
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str) -> logging.Logger:
    """Erstellt einen Logger mit File- und Console-Handler"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Formatierung
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File Handler für lokale Logs
    file_handler = logging.FileHandler(
        LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m')}.log"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console Handler für Railway/Docker Logs
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Erstelle Standard-Logger
api_logger = setup_logger("api")
db_logger = setup_logger("db")
scraper_logger = setup_logger("scraper") 