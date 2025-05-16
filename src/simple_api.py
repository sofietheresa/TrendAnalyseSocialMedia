"""
Simple API for model drift endpoint
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model registry path
MODEL_REGISTRY_PATH = Path("models/registry").resolve()

# Define the DriftMetrics model
class DriftMetrics(BaseModel):
    timestamp: str
    dataset_drift: bool
    share_of_drifted_columns: float
    drifted_columns: List[str]

@app.get("/")
async def root():
    return {"message": "Simple API running"}

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
                return DriftMetrics(**drift_metrics)
        else:
            logger.warning(f"No drift metrics found at {drift_path}, using mock data")
    except Exception as e:
        logger.error(f"Error accessing drift metrics: {e}")
    
    # Return mock drift metrics if no actual metrics found
    return DriftMetrics(
        timestamp=datetime.now().isoformat(),
        dataset_drift=True,
        share_of_drifted_columns=0.25,
        drifted_columns=["text_length", "sentiment_score", "engagement_rate"]
    ) 