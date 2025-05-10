from fastapi import FastAPI, HTTPException
from src.pipelines import social_media_analysis_pipeline
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
    title="Social Media Analysis API",
    description="API für die Analyse von Social Media Trends",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "message": "Willkommen bei der Social Media Analysis API",
        "endpoints": {
            "GET /": "Diese Hilfeseite",
            "POST /run-pipeline": "Startet die Analyse-Pipeline",
            "GET /status": "Zeigt den Status der letzten Analyse",
            "GET /metrics": "Prometheus Metriken"
        }
    }

@app.post("/run-pipeline")
def run_pipeline():
    PIPELINE_RUNS.inc()
    start_time = time.time()
    
    try:
        # Pipeline starten
        pipeline = social_media_analysis_pipeline()
        pipeline.run()
        
        # Ergebnisse laden
        results_dir = Path("data/processed")
        results = {}
        
        # Exploration Results
        if (results_dir / "exploration_results.json").exists():
            with open(results_dir / "exploration_results.json", "r") as f:
                results["exploration"] = json.load(f)
        
        # Prediction Results
        if (results_dir / "prediction_results.json").exists():
            with open(results_dir / "prediction_results.json", "r") as f:
                results["prediction"] = json.load(f)
        
        duration = time.time() - start_time
        PIPELINE_DURATION.observe(duration)
        
        return {
            "status": "success",
            "message": "Pipeline erfolgreich ausgeführt",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "results": results
        }
    
    except Exception as e:
        PIPELINE_ERRORS.inc()
        logger.error(f"Pipeline fehlgeschlagen: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
def get_status():
    try:
        results_dir = Path("data/processed")
        status = {
            "last_update": None,
            "has_results": False,
            "available_results": []
        }
        
        if results_dir.exists():
            # Prüfe auf vorhandene Ergebnisdateien
            result_files = list(results_dir.glob("*.json"))
            if result_files:
                status["has_results"] = True
                status["available_results"] = [f.name for f in result_files]
                # Finde das neueste Update
                latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
                status["last_update"] = datetime.fromtimestamp(
                    latest_file.stat().st_mtime
                ).isoformat()
        
        return status
    
    except Exception as e:
        logger.error(f"Statusabfrage fehlgeschlagen: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 