import requests
import time
import logging
from dotenv import load_dotenv# lokal!

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scheduler.run_all_scrapers import run_all  

load_dotenv()

RENDER_URL = os.getenv("RENDER_URL", "https://trendanalysesocialmedia.onrender.com")
API_SECRET = os.getenv("API_SECRET")

HEADERS = {
    "Authorization": f"Bearer {API_SECRET}"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def get_job():
    try:
        r = requests.get(f"{RENDER_URL}/scrape-job", headers=HEADERS)
        r.raise_for_status()
        return r.json().get("job")
    except Exception as e:
        logging.error(f"Fehler beim Abrufen des Jobs: {e}")
        return None

if __name__ == "__main__":
    logging.info("🚀 Starte lokalen Scraper-Worker")
    while True:
        job = get_job()
        if job:
            logging.info(f"📥 Job erhalten: {job}")
            try:
                run_all()
                logging.info("✅ Scraper lokal erfolgreich ausgeführt")
            except Exception as e:
                logging.error(f"❌ Fehler beim lokalen Scraping: {e}")
        else:
            logging.info("🔄 Kein neuer Job – warte ...")
        time.sleep(60)
