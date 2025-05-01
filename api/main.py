import logging
from fastapi import FastAPI

# Versuch den Import
try:
    from scheduler.run_all_scrapers import run_all
    logging.info("✅ run_all erfolgreich importiert")
except Exception as e:
    logging.exception("❌ Fehler beim Import von run_all")

app = FastAPI()

@app.get("/")
def root():
    logging.info("GET / aufgerufen")
    return {"status": "ok"}

@app.post("/run-scrapers")
def run_scrapers():
    logging.info("POST /run-scrapers aufgerufen")
    try:
        run_all()
        logging.info("✅ run_all wurde ausgeführt")
        return {"status": "scraping started"}
    except Exception as e:
        logging.exception("❌ Fehler beim Ausführen von run_all")
        return {"status": "error", "detail": str(e)}
