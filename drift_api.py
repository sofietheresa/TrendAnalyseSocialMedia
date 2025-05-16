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
from fastapi import FastAPI, Query, HTTPException
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

# Define models
class DriftMetrics(BaseModel):
    timestamp: str
    dataset_drift: bool
    share_of_drifted_columns: float
    drifted_columns: List[str]

class PipelineExecution(BaseModel):
    id: str
    pipelineId: str
    startTime: str
    endTime: Optional[str] = None
    status: str
    trigger: str

@app.get("/")
async def root():
    return {"message": "Model Drift API running"}

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.get("/debug/routes")
async def debug_routes():
    """
    List all available routes for debugging
    """
    routes = [
        {"path": route.path, "name": route.name, "methods": route.methods}
        for route in app.routes
    ]
    return {"routes": routes}

@app.get("/api/mlops/pipelines")
async def get_pipelines():
    """
    Get all ML pipelines status
    """
    logger.info("Request for all pipelines")
    
    # Return mock pipeline data
    pipelines = {
        "trend_analysis": {
            "name": "Trend Analysis Pipeline",
            "description": "Analyzes trends across social media platforms",
            "steps": [
                {"id": "data_ingestion", "name": "Data Ingestion", "description": "Collects data from social media APIs", "status": "completed", "runtime": "00:05:23"},
                {"id": "preprocessing", "name": "Preprocessing", "description": "Cleans and prepares data for analysis", "status": "completed", "runtime": "00:08:47"},
                {"id": "topic_modeling", "name": "Topic Modeling", "description": "Identifies key topics in the content", "status": "completed", "runtime": "00:15:32"},
                {"id": "sentiment_analysis", "name": "Sentiment Analysis", "description": "Determines sentiment for each post", "status": "completed", "runtime": "00:09:18"},
                {"id": "trend_detection", "name": "Trend Detection", "description": "Identifies emerging trends in topics", "status": "completed", "runtime": "00:06:42"},
                {"id": "model_evaluation", "name": "Model Evaluation", "description": "Evaluates the performance of prediction models", "status": "completed", "runtime": "00:03:55"},
                {"id": "visualization", "name": "Visualization", "description": "Prepares data for dashboard visualization", "status": "completed", "runtime": "00:02:11"}
            ],
            "lastRun": "2023-12-15T14:30:22",
            "nextScheduledRun": "2023-12-16T14:30:00",
            "averageRuntime": "00:51:48",
            "status": "completed"
        }
    }
    
    return pipelines

@app.get("/api/mlops/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    """
    Get details for a specific pipeline
    """
    logger.info(f"Request for pipeline: {pipeline_id}")
    
    pipelines = {
        "trend_analysis": {
            "name": "Trend Analysis Pipeline",
            "description": "Analyzes trends across social media platforms",
            "steps": [
                {"id": "data_ingestion", "name": "Data Ingestion", "description": "Collects data from social media APIs", "status": "completed", "runtime": "00:05:23"},
                {"id": "preprocessing", "name": "Preprocessing", "description": "Cleans and prepares data for analysis", "status": "completed", "runtime": "00:08:47"},
                {"id": "topic_modeling", "name": "Topic Modeling", "description": "Identifies key topics in the content", "status": "completed", "runtime": "00:15:32"},
                {"id": "sentiment_analysis", "name": "Sentiment Analysis", "description": "Determines sentiment for each post", "status": "completed", "runtime": "00:09:18"},
                {"id": "trend_detection", "name": "Trend Detection", "description": "Identifies emerging trends in topics", "status": "completed", "runtime": "00:06:42"},
                {"id": "model_evaluation", "name": "Model Evaluation", "description": "Evaluates the performance of prediction models", "status": "completed", "runtime": "00:03:55"},
                {"id": "visualization", "name": "Visualization", "description": "Prepares data for dashboard visualization", "status": "completed", "runtime": "00:02:11"}
            ],
            "lastRun": "2023-12-15T14:30:22",
            "nextScheduledRun": "2023-12-16T14:30:00",
            "averageRuntime": "00:51:48",
            "status": "completed"
        }
    }
    
    if pipeline_id not in pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
    
    return pipelines[pipeline_id]

@app.get("/api/mlops/pipelines/{pipeline_id}/executions")
async def get_pipeline_executions(pipeline_id: str):
    """
    Get executions for a specific pipeline
    """
    logger.info(f"Request for executions of pipeline: {pipeline_id}")
    
    # Mock executions - in production this would be retrieved from a database
    all_executions = [
        {"id": "exec-001", "pipelineId": "trend_analysis", "startTime": "2023-12-15T14:30:22", "endTime": "2023-12-15T15:22:10", "status": "completed", "trigger": "scheduled"},
        {"id": "exec-002", "pipelineId": "trend_analysis", "startTime": "2023-12-14T14:30:15", "endTime": "2023-12-14T15:24:02", "status": "completed", "trigger": "scheduled"},
        {"id": "exec-003", "pipelineId": "realtime_monitoring", "startTime": "2023-12-15T16:45:10", "endTime": None, "status": "running", "trigger": "manual"},
        {"id": "exec-004", "pipelineId": "model_training", "startTime": "2023-12-14T09:15:33", "endTime": "2023-12-14T11:16:57", "status": "failed", "trigger": "manual"},
        {"id": "exec-005", "pipelineId": "trend_analysis", "startTime": "2023-12-13T14:30:18", "endTime": "2023-12-13T15:25:33", "status": "completed", "trigger": "scheduled"},
    ]
    
    executions = [execution for execution in all_executions if execution["pipelineId"] == pipeline_id]
    
    return executions

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

@app.post("/api/mlops/pipelines/{pipeline_id}/execute")
async def execute_pipeline(pipeline_id: str):
    """
    Execute a specific pipeline
    """
    logger.info(f"Request to execute pipeline: {pipeline_id}")
    
    # Map pipeline ID to model name
    pipeline_to_model = {
        "trend_analysis": "topic_model",
        "realtime_monitoring": "anomaly_detector",
        "model_training": "sentiment_classifier"
    }
    
    if pipeline_id not in pipeline_to_model:
        logger.error(f"Pipeline {pipeline_id} not found")
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
    
    # Generate execution ID
    execution_id = f"exec-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # In a real implementation, this would start the pipeline in a background task
    
    response = {
        "execution_id": execution_id,
        "pipeline_id": pipeline_id,
        "status": "started",
        "startTime": datetime.now().isoformat(),
        "message": f"Pipeline {pipeline_id} execution started with ID {execution_id}"
    }
    
    logger.info(f"Pipeline execution response: {response}")
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    logger.info(f"Starting Model Drift API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 