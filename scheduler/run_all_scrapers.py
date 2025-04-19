import subprocess
import logging
from datetime import datetime

# Logging einrichten
logfile = "logs/scraper.log"
logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

SCRAPER_SCRIPTS = [
    "reddit_scraper.py",
    "twitter_scraper.py",
    "tiktok_scraper.py",
    "instagram_scraper.py",
    "youtube_scraper.py"
]

def run_script(script):
    logging.info(f"🔄 Starte {script}")
    try:
        start = datetime.now()
        result = subprocess.run(
            ["python", f"app/src/{script}"],
            capture_output=True,
            text=True,
            check=True
        )
        duration = (datetime.now() - start).seconds
        logging.info(f"✅ {script} erfolgreich in {duration} Sekunden.")
        logging.debug(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Fehler beim Ausführen von {script}")
        logging.error(e.stderr)

def run_all():
    logging.info("🚀 Sammle Social Media Trends...")
    for script in SCRAPER_SCRIPTS:
        run_script(script)
    logging.info("🎉 Alle Scraper abgeschlossen.")

if __name__ == "__main__":
    run_all()
