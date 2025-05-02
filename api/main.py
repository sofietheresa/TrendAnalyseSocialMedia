import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from scheduler.run_all_scrapers import run_all
from dotenv import load_dotenv

# .env laden
load_dotenv()

API_SECRET = os.getenv("API_SECRET")

# Logging
logging.basicConfig(
    level=logging.INFO,
    filemode="a" ,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = FastAPI()

# Root Endpoint
@app.get("/")
def root():
    logging.info("GET / aufgerufen")
    return {"status": "ok"}

# Trigger Scraper
@app.post("/run-scrapers")
def run_scrapers(request: Request):
    logging.info("POST /run-scrapers aufgerufen")

    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {API_SECRET}":
        logging.warning("❌ Ungültiger oder fehlender Authorization-Header")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        run_all()
        logging.info("✅ run_all wurde ausgeführt")
        return {"status": "scraping started"}
    except Exception as e:
        logging.exception("❌ Fehler beim Ausführen von run_all")
        raise HTTPException(status_code=500, detail=str(e))

# CSV-Dateien herunterladen
@app.get("/data/download/{filename}")
def download_data(filename: str, request: Request):
    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {API_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    filepath = f"/app/data/raw/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")

    return FileResponse(path=filepath, filename=filename)

# Log-Dateien herunterladen
@app.get("/logs/download/{filename}")
def download_log(filename: str, request: Request):
    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {API_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    filepath = f"/app/logs/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Logdatei nicht gefunden")

    return FileResponse(path=filepath, filename=filename)
