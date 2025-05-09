import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from pathlib import Path
import zipfile
import io

# 🔐 Konfiguration & Logging
load_dotenv()
API_SECRET = os.getenv("API_SECRET")
app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# 🗂 Job-Warteschlange (einfache Strings wie "run_all" oder "reddit")
scraping_job_queue = []

# 🔐 Autorisierung prüfen
def authorize(request: Request):
    token = request.headers.get("Authorization") or request.query_params.get("token")
    if token != f"Bearer {API_SECRET}" and token != API_SECRET:
        logging.warning("❌ Ungültiger oder fehlender Token")
        raise HTTPException(status_code=401, detail="Unauthorized")

# 🧪 Basis-Check
@app.get("/")
def root():
    logging.info("GET / aufgerufen")
    return {"status": "ok"}

# 🚀 Job zur Warteschlange hinzufügen
@app.post("/run-scrapers")
def run_scrapers(request: Request):
    logging.info("POST /run-scrapers aufgerufen")
    authorize(request)
    scraping_job_queue.append("run_all")
    logging.info("✅ Scrape-Auftrag zur Warteschlange hinzugefügt")
    return {"status": "scraping job queued"}

# 🧾 Job für Worker bereitstellen
@app.get("/scrape-job")
def get_scrape_job(request: Request):
    authorize(request)
    if scraping_job_queue:
        job = scraping_job_queue.pop(0)
        logging.info(f"🎯 Scrape-Auftrag '{job}' an Client übergeben")
        return {"job": job}
    logging.info("ℹ️ Kein Job in Warteschlange")
    return {"job": None}

# ⬇️ Einzelne CSV-Datei herunterladen
@app.get("/data/download/{filename}")
def download_data(filename: str, request: Request):
    authorize(request)
    filepath = Path("/app/data/raw") / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    return FileResponse(path=filepath, filename=filename)

# ⬇️ Einzelne Logdatei herunterladen
@app.get("/logs/download/{filename}")
def download_log(filename: str, request: Request):
    authorize(request)
    filepath = Path("/app/logs") / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Logdatei nicht gefunden")
    return FileResponse(path=filepath, filename=filename)

# ⬇️ Alle CSV-Dateien als ZIP
@app.get("/data/download/all")
def download_all_data(request: Request):
    authorize(request)
    data_dir = Path("/app/data/raw")
    if not data_dir.exists():
        raise HTTPException(status_code=404, detail="Datenverzeichnis nicht gefunden")

    zip_stream = io.BytesIO()
    with zipfile.ZipFile(zip_stream, mode="w") as zf:
        for file in data_dir.glob("*.csv"):
            zf.write(file, arcname=file.name)
    zip_stream.seek(0)

    return StreamingResponse(
        zip_stream,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=data_all.zip"}
    )
