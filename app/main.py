from fastapi import FastAPI
import logging
import sys
import os

# Einfache Logging-Konfiguration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Starte mit einer Nachricht, die im Log sichtbar sein sollte
logger.info("=== APPLICATION STARTING ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
logger.info(f"Port: {os.getenv('PORT', '8080')}")

# Erstelle eine minimalistische FastAPI Anwendung
app = FastAPI(
    title="Minimal API",
    description="Minimale API für Fehlerbehebung",
    version="1.0.0"
)

# Nur Basis-Endpunkte ohne Datenbankverbindung
@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {
        "status": "online",
        "message": "Minimal API is running",
        "timestamp": None  # Keine datetime-Importe, um jede mögliche Fehlerquelle auszuschließen
    }

@app.get("/health")
async def health_check():
    logger.info("Health endpoint called")
    return {
        "status": "healthy",
        "minimal_mode": True
    }

@app.get("/info")
async def info():
    logger.info("Info endpoint called")
    # Filtere sensible Umgebungsvariablen
    safe_env_vars = {}
    for k, v in os.environ.items():
        k_lower = k.lower()
        if "password" not in k_lower and "secret" not in k_lower and "key" not in k_lower:
            safe_env_vars[k] = v
            
    return {
        "python_version": sys.version,
        "environment_variables": safe_env_vars,
        "working_directory": os.getcwd(),
        "files_in_directory": os.listdir()
    }

# Keine weiteren Endpunkte oder Komplexität 