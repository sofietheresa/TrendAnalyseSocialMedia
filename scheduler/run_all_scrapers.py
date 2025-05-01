import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Eigener Logger für den Scheduler
logger = logging.getLogger("trendsage.scheduler")
logger.setLevel(logging.INFO)

# Optional: Stelle sicher, dass ein Handler existiert
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Alternativ: Datei zusätzlich
Path("logs").mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler("logs/scraper.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

SCRAPER_SCRIPTS = [
    "scheduler/jobs/reddit_scraper.py",
    "scheduler/jobs/tiktok_scraper.py",
    "scheduler/jobs/youtube_scraper.py"
]

def run_script(script):
    logger.info(f"Starte {script}")
    try:
        start = datetime.now()
        result = subprocess.run(
            ["python", script],
            capture_output=True,
            text=True,
            check=True
        )
        duration = (datetime.now() - start).seconds
        logger.info(f"{script} erfolgreich in {duration} Sekunden.")
        logger.debug(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Fehler beim Ausführen von {script}")
        logger.error(e.stderr)

def run_all():
    logger.info("Starte alle Scraper...")
    for script in SCRAPER_SCRIPTS:
        run_script(script)
    logger.info("Alle Scraper abgeschlossen.")
