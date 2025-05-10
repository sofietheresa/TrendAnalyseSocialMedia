from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from zenml.client import Client
from zenml.pipelines import pipeline
from zenml.steps import step
import os
from typing import Dict, Any
import logging
from pathlib import Path
import json
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus Metriken
PIPELINE_RUNS = Counter('pipeline_runs_total', 'Total number of pipeline runs')
PIPELINE_DURATION = Histogram('pipeline_duration_seconds', 'Time spent running pipeline')
PIPELINE_ERRORS = Counter('pipeline_errors_total', 'Total number of pipeline errors')

app = FastAPI(
    title="Social Media Trend Analysis API",
    description="API für die Analyse von Social Media Trends",
    version="1.0.0"
)

# CORS-Konfiguration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion auf spezifische Domains beschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipeline-Client initialisieren
client = Client()

@app.get("/")
async def root():
    return {"message": "Social Media Trend Analysis API"}

@app.post("/api/run-pipeline/{step}")
async def run_pipeline_step(step: str):
    try:
        # Pipeline-Schritt ausführen
        if step == "data_ingestion":
            pipeline_instance = client.get_pipeline("data_ingestion_pipeline")
        elif step == "preprocessing":
            pipeline_instance = client.get_pipeline("preprocessing_pipeline")
        elif step == "data_exploration":
            pipeline_instance = client.get_pipeline("data_exploration_pipeline")
        elif step == "prediction":
            pipeline_instance = client.get_pipeline("prediction_pipeline")
        else:
            raise HTTPException(status_code=400, detail=f"Unbekannter Pipeline-Schritt: {step}")

        # Pipeline ausführen
        run = pipeline_instance.run()
        
        return {
            "status": "success",
            "step": step,
            "run_id": run.id,
            "message": f"Pipeline-Schritt '{step}' erfolgreich ausgeführt"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run-pipeline")
async def run_full_pipeline():
    try:
        # Alle Pipeline-Schritte nacheinander ausführen
        steps = ["data_ingestion", "preprocessing", "data_exploration", "prediction"]
        results = {}
        
        for step in steps:
            pipeline_instance = client.get_pipeline(f"{step}_pipeline")
            run = pipeline_instance.run()
            results[step] = {
                "run_id": run.id,
                "status": "completed"
            }
        
        return {
            "status": "success",
            "message": "Vollständige Pipeline erfolgreich ausgeführt",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    try:
        # Status der letzten Pipeline-Ausführungen abrufen
        status = {}
        steps = ["data_ingestion", "preprocessing", "data_exploration", "prediction"]
        
        for step in steps:
            pipeline_instance = client.get_pipeline(f"{step}_pipeline")
            runs = pipeline_instance.get_runs(limit=1)
            if runs:
                status[step] = {
                    "last_run": runs[0].id,
                    "status": runs[0].status,
                    "timestamp": runs[0].created_at.isoformat()
                }
            else:
                status[step] = {
                    "status": "no_runs",
                    "message": "Keine Pipeline-Ausführungen gefunden"
                }
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 