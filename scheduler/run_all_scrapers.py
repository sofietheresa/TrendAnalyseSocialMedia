import subprocess
import os
from datetime import datetime
from pathlib import Path
import logging
import glob

# 🔧 sicherstellen, dass logs-Verzeichnis vorhanden ist
Path("/app/logs").mkdir(parents=True, exist_ok=True)

# Automatisch alle *_scraper.py Dateien im jobs/ Verzeichnis laden
SCRAPER_SCRIPTS = sorted(glob.glob("jobs/*_scraper.py"))

def run_script(script):
    name = Path(script).stem.replace("_scraper", "")
    log_file = Path("/app/logs") / f"{name}.log"

    logging.info(f"🔍 Checking script: {script}")
    print(f"📄 Log-Datei: {log_file}")
    print(f"▶️  Starte {script} ...")

    start = datetime.now()

    try:
        with open(log_file, "a", encoding="utf-8") as log:
            subprocess.run(
                ["python", script],
                cwd="scheduler",
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
        run_script(script)

if __name__ == "__main__":
    run_all()
