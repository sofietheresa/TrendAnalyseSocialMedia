import requests
import logging
from pathlib import Path
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import schedule
import time

# Lade Umgebungsvariablen
load_dotenv()

# Konfiguration
API_KEY = os.getenv("API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def send_to_backend(data: list) -> bool:
    """Sendet gescrapte Daten an das Backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/sync",
            json={"data": data},
            headers={"API_KEY": API_KEY}
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Sync erfolgreich: {result}")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Senden der Daten: {e}")
        return False

def run_scrapers():
    """Führt alle Scraper aus und sendet die Daten"""
    try:
        # Hier werden Ihre bestehenden Scraper aufgerufen
        # Beispiel:
        from scrapers.reddit_scraper import scrape_reddit
        from scrapers.tiktok_scraper import scrape_tiktok
        from scrapers.youtube_scraper import scrape_youtube
        
        all_data = []
        
        # Reddit
        try:
            reddit_data = scrape_reddit()
            all_data.extend(reddit_data)
            logger.info(f"{len(reddit_data)} Reddit-Posts gescrapt")
        except Exception as e:
            logger.error(f"Fehler beim Reddit-Scraping: {e}")
        
        # TikTok
        try:
            tiktok_data = scrape_tiktok()
            all_data.extend(tiktok_data)
            logger.info(f"{len(tiktok_data)} TikTok-Posts gescrapt")
        except Exception as e:
            logger.error(f"Fehler beim TikTok-Scraping: {e}")
        
        # YouTube
        try:
            youtube_data = scrape_youtube()
            all_data.extend(youtube_data)
            logger.info(f"{len(youtube_data)} YouTube-Posts gescrapt")
        except Exception as e:
            logger.error(f"Fehler beim YouTube-Scraping: {e}")
        
        if all_data:
            success = send_to_backend(all_data)
            if success:
                logger.info(f"Erfolgreich {len(all_data)} Einträge synchronisiert")
            else:
                logger.error("Fehler bei der Synchronisation")
        else:
            logger.warning("Keine Daten zum Synchronisieren gefunden")
            
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}")

def schedule_scraping():
    """Plant regelmäßiges Scraping"""
    # Scraping alle 6 Stunden
    schedule.every(6).hours.do(run_scrapers)
    
    # Initiales Scraping
    logger.info("Starte initiales Scraping...")
    run_scrapers()
    
    # Endlosschleife für den Scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    logger.info("Scraper-Client gestartet")
    schedule_scraping() 