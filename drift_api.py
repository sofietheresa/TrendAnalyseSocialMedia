"""
Simple API server dedicated to serving the model drift endpoint
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("drift_api")

# Create app
app = FastAPI(
    title="Model Drift API",
    description="API for serving model drift metrics",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model registry path
MODEL_REGISTRY_PATH = Path("models/registry").resolve()
MODEL_REGISTRY_PATH.mkdir(parents=True, exist_ok=True)

# Ensure topic model directory exists
TOPIC_MODEL_PATH = MODEL_REGISTRY_PATH / "topic_model" / "v1.0.2"
TOPIC_MODEL_PATH.mkdir(parents=True, exist_ok=True)

# Create drift metrics file if it doesn't exist
DRIFT_METRICS_PATH = TOPIC_MODEL_PATH / "drift_metrics.json"
if not DRIFT_METRICS_PATH.exists():
    MOCK_DRIFT = {
        "timestamp": datetime.now().isoformat(),
        "dataset_drift": True,
        "share_of_drifted_columns": 0.25,
        "drifted_columns": ["text_length", "sentiment_score", "engagement_rate"]
    }
    with open(DRIFT_METRICS_PATH, "w") as f:
        json.dump(MOCK_DRIFT, f, indent=2)
    logger.info(f"Created mock drift metrics file at {DRIFT_METRICS_PATH}")

# Define the DriftMetrics model
class DriftMetrics(BaseModel):
    timestamp: str
    dataset_drift: bool
    share_of_drifted_columns: float
    drifted_columns: List[str]

@app.get("/")
async def root():
    return {"message": "Model Drift API running"}

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.get("/api/mlops/models/{model_name}/drift", response_model=DriftMetrics)
async def get_model_drift(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version")
):
    """
    Get data drift metrics for a specific model version
    """
    logger.info(f"Request for drift metrics of model: {model_name}, version: {version}")
    
    # Set default version if not provided
    if not version:
        version = "v1.0.2"  # Default to latest version
        logger.info(f"No version specified, using default: {version}")
    
    # Check for actual drift metrics in model registry
    drift_path = MODEL_REGISTRY_PATH / model_name / version / "drift_metrics.json"
    logger.info(f"Checking for drift metrics at: {drift_path}")
    
    try:
        if drift_path.exists():
            logger.info(f"Found drift metrics at {drift_path}")
            with open(drift_path, "r") as f:
                drift_metrics = json.load(f)
                result = DriftMetrics(**drift_metrics)
                logger.info(f"Returning drift metrics: {result}")
                return result
        else:
            logger.warning(f"No drift metrics found at {drift_path}, using mock data")
    except Exception as e:
        logger.error(f"Error accessing drift metrics: {e}")
    
    # Return mock drift metrics if no actual metrics found
    result = DriftMetrics(
        timestamp=datetime.now().isoformat(),
        dataset_drift=True,
        share_of_drifted_columns=0.25,
        drifted_columns=["text_length", "sentiment_score", "engagement_rate"]
    )
    logger.info(f"Returning mock drift metrics: {result}")
    return result

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Model Drift API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 