import logging
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from fastapi.responses import FileResponse
import zipfile
import tempfile

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

    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {API_SECRET}":
        logging.warning("❌ Ungültiger oder fehlender Authorization-Header")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        run_all()
        logging.info("✅ run_all wurde ausgeführt")

        # Zip-Datei im temporären Verzeichnis erstellen
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            zip_path = tmp.name
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for folder in ["/app/data/raw", "/app/logs"]:
                    for root, _, files in os.walk(folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, start="/app")
                            zipf.write(file_path, arcname)

        logging.info(f"📦 Dateien gezippt unter {zip_path}")
        return FileResponse(path=zip_path, filename="scraper_output.zip", media_type="application/zip")

    except Exception as e:
        logging.exception("❌ Fehler beim Ausführen von run_all")
        raise HTTPException(status_code=500, detail=str(e))

    
@app.get("/data/download/{filename}")
def download_data_file(filename: str, request: Request):
    if request.headers.get("Authorization") != f"Bearer {API_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    path = f"/app/data/raw/{filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")

    return FileResponse(path=path, filename=filename)

@app.get("/logs/download/{filename}")
def download_log_file(filename: str, request: Request):
    if request.headers.get("Authorization") != f"Bearer {API_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    path = f"/app/logs/{filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Log nicht gefunden")

    return FileResponse(path=path, filename=filename)
