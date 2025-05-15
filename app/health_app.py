from fastapi import FastAPI
import logging
from datetime import datetime

# Einfache Logging-Konfiguration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("health-app")

# Minimale FastAPI-App nur für den Healthcheck
app = FastAPI(
    title="Health Check Service",
    description="Minimal service for Railway health checks",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Basis-Endpunkt für Healthcheck"""
    logger.info("Root-Healthcheck aufgerufen")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health():
    """Einfacher Healthcheck-Endpunkt"""
    logger.info("Health-Endpunkt aufgerufen")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/railway-health")
async def railway_health():
    """Railway-spezifischer Healthcheck"""
    logger.info("Railway-Health-Endpunkt aufgerufen")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Wenn diese Datei direkt ausgeführt wird
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 