import logging
import os
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

# .env laden (nur lokal relevant)
load_dotenv()

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Versuch den Import
try:
    from scheduler.run_all_scrapers import run_all
    logging.info("✅ run_all erfolgreich importiert")
except Exception as e:
    logging.exception("❌ Fehler beim Import von run_all")

# FastAPI App
app = FastAPI()

# Secret aus Umgebungsvariable laden
API_SECRET = os.getenv("API_SECRET")

@app.get("/")
def root():
    logging.info("GET / aufgerufen")
    return {"status": "ok"}

@app.post("/run-scrapers")
def run_scrapers(request: Request):
    logging.info("POST /run-scrapers aufgerufen")

    # Authorization Header prüfen
    auth_header = request.headers.get("Authorization")
    expected = f"Bearer {API_SECRET}"

    if auth_header != expected:
        logging.warning("❌ Ungültiger oder fehlender Authorization-Header")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        run_all()
        logging.info("✅ run_all wurde ausgeführt")
        return {"status": "scraping started"}
    except Exception as e:
        logging.exception("❌ Fehler beim Ausführen von run_all")
        return {"status": "error", "detail": str(e)}
