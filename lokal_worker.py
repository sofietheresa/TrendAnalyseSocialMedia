import requests
import time
import logging
from scheduler.run_all_scrapers import run_all  # das ist dein existierender Scraper

RENDER_URL = "https://deine-app.onrender.com"
API_SECRET = "dein_token"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

HEADERS = {
    "Authorization": f"Bearer {API_SECRET}"
}

def get_job():
    try:
        r = requests.get(f"{RENDER_URL}/scrape-job", headers=HEADERS)
        r.raise_for_status()
        return r.json().get("job")
    except Exception as e:
        logging.error(f"❌ Fehler beim Abrufen des Jobs: {e}")
        return None

while True:
    job = get_job()
    if job:
        logging.info(f"📥 Job empfangen: {job}")
        try:
            run_all()
            logging.info("✅ Scraper erfolgreich ausgeführt")
        except Exception as e:
            logging.error(f"❌ Fehler beim Scraping: {e}")
    else:
        logging.info("🔄 Kein Job vorhanden, warte ...")

    time.sleep(30)
