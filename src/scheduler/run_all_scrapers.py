import os
import subprocess
from datetime import datetime
from pathlib import Path
import logging
import glob
import importlib

# 🔧 sicherstellen, dass logs-Verzeichnis vorhanden ist
Path("logs").mkdir(parents=True, exist_ok=True)

# Automatisch alle *_scraper.py Dateien im jobs/ Verzeichnis laden
BASE_DIR = Path(__file__).resolve().parent
JOBS_DIR = BASE_DIR / "jobs"
SCRAPER_SCRIPTS = sorted(JOBS_DIR.glob("*_scraper.py"))

def run_script(script):
    name = Path(script).stem.replace("_scraper", "")
    log_file = Path("logs") / f"{name}.log"

    
    print(f"📄 Log-Datei: {log_file}")
    print(f"▶️  Starte {script} ...")

    start = datetime.now()

    try:
        relative_script_path = script.relative_to(BASE_DIR)
        with open(log_file, "a", encoding="utf-8") as log:
            subprocess.run(
                ["python", str(relative_script_path)],
                cwd=str(BASE_DIR),
                env=os.environ.copy(),
                stdout=log,
                stderr=log,
                text=True,
                check=True
            )
        duration = (datetime.now() - start).seconds
        print(f"✅  {script} erfolgreich in {duration} Sekunden.")

    except subprocess.CalledProcessError:
        logging.error(f"❌ Fehler beim Ausführen von {script} (siehe {log_file})")
        print(f"❌ Fehler beim Ausführen von {script} (siehe {log_file})")

def run_all():
    
    for script in SCRAPER_SCRIPTS:
        logging.info("Attemping to run script: %s", script)
        run_script(script)

if __name__ == "__main__":
    run_all()
