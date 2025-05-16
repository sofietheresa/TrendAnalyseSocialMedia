"""
Direct routes for the API

This module contains direct route handlers that will be registered directly on the FastAPI app
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Create router
direct_router = APIRouter()

# Model registry path
MODEL_REGISTRY_PATH = Path("models/registry").resolve()

# Define the DriftMetrics model
class DriftMetrics(BaseModel):
    timestamp: str
    dataset_drift: bool
    share_of_drifted_columns: float
    drifted_columns: List[str]

@direct_router.get("/api/mlops/models/{model_name}/drift", response_model=DriftMetrics)
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
    
    if drift_path.exists():
        logger.info(f"Found drift metrics at {drift_path}")
        try:
            with open(drift_path, "r") as f:
                drift_metrics = json.load(f)
                return DriftMetrics(**drift_metrics)
        except Exception as e:
            logger.error(f"Error reading drift metrics: {e}")
    else:
        logger.warning(f"No drift metrics found at {drift_path}, using mock data")
    
    # Return mock drift metrics if no actual metrics found
    return DriftMetrics(
        timestamp=datetime.now().isoformat(),
        dataset_drift=True,
        share_of_drifted_columns=0.25,
        drifted_columns=["text_length", "sentiment_score", "engagement_rate"]
    ) 