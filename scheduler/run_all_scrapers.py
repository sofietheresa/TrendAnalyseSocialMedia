import subprocess
import os
from datetime import datetime
from pathlib import Path

# 🔧 sicherstellen, dass logs-Verzeichnis vorhanden ist
Path("/app/logs").mkdir(parents=True, exist_ok=True)

# Liste der zu startenden Scraper (relativ zu scheduler/)
SCRAPER_SCRIPTS = [
    "jobs/reddit_scraper.py",
    "jobs/tiktok_scraper.py",
    "jobs/youtube_scraper.py"
]

def run_script(script):
    name = script.split("/")[-1].replace("_scraper.py", "")
    log_file = Path("/app/logs") / f"{name}.log"

    print(f"📄 Log-Datei: {log_file}")
    print(f"▶️  Starte {script} ...")

    start = datetime.now()

    # Logfile einmalig öffnen und stdout/stderr hineinschreiben
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
        print(f"❌ Fehler beim Ausführen von {script} (siehe {log_file})")

        print(f"❌ Fehler beim Ausführen von {script} (siehe {log_file})")


def run_all():
    for script in SCRAPER_SCRIPTS:
        run_script(script)

if __name__ == "__main__":
    run_all()
