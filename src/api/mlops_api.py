"""
ML OPS API Module

This module implements API endpoints for ML Operations to communicate with the frontend.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.pipelines.mlops_pipeline import MLOpsPipeline, run_mlops_pipeline
from src.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# Model registry path
MODEL_REGISTRY_PATH = Path("models/registry").resolve()

# Create API router
router = APIRouter()

# Define response models
class PipelineStatus(BaseModel):
    name: str
    description: str
    status: str
    steps: List[Dict[str, Any]]
    lastRun: str
    nextScheduledRun: str
    averageRuntime: str

class ModelVersion(BaseModel):
    id: str
    name: str
    date: str
    status: str

class ModelMetrics(BaseModel):
    coherence_score: float = Field(..., description="Topic coherence score")
    diversity_score: float = Field(..., description="Topic diversity score")
    document_coverage: float = Field(..., description="Document coverage")
    total_documents: int = Field(..., description="Total number of documents")
    uniqueness_score: Optional[float] = None
    silhouette_score: Optional[float] = None
    topic_separation: Optional[float] = None
    avg_topic_similarity: Optional[float] = None
    execution_time: Optional[float] = None
    topic_quality: Optional[float] = None

class PipelineExecution(BaseModel):
    id: str
    pipelineId: str
    startTime: str
    endTime: Optional[str] = None
    status: str
    trigger: str

class DriftMetrics(BaseModel):
    timestamp: str
    dataset_drift: bool
    share_of_drifted_columns: float
    drifted_columns: List[str]

@router.get("/pipelines", response_model=Dict[str, PipelineStatus])
async def get_pipelines():
    """
    Get all ML pipelines status
    """
    logger.info("Request for all pipelines")
    
    # In production, this would retrieve from a database or the actual pipeline status
    # For now, we return mock data similar to the frontend
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
        },
        
        "realtime_monitoring": {
            "name": "Realtime Monitoring Pipeline",
            "description": "Monitors social media in real-time for emerging trends",
            "steps": [
                {"id": "stream_ingestion", "name": "Stream Ingestion", "description": "Collects streaming data from social APIs", "status": "completed", "runtime": "00:01:02"},
                {"id": "realtime_preprocessing", "name": "Realtime Preprocessing", "description": "Preprocesses streaming data", "status": "completed", "runtime": "00:00:48"},
                {"id": "anomaly_detection", "name": "Anomaly Detection", "description": "Detects unusual patterns in real-time", "status": "running", "runtime": "00:02:15"},
                {"id": "alert_generation", "name": "Alert Generation", "description": "Generates alerts for detected anomalies", "status": "pending", "runtime": "00:00:00"},
                {"id": "dashboard_update", "name": "Dashboard Update", "description": "Updates the real-time dashboard", "status": "pending", "runtime": "00:00:00"}
            ],
            "lastRun": "2023-12-15T16:45:10",
            "nextScheduledRun": "continuous",
            "averageRuntime": "00:10:22",
            "status": "running"
        },
        
        "model_training": {
            "name": "Model Training Pipeline",
            "description": "Trains and deploys ML models for trend prediction",
            "steps": [
                {"id": "data_collection", "name": "Data Collection", "description": "Collects historical data for training", "status": "completed", "runtime": "00:12:45"},
                {"id": "feature_engineering", "name": "Feature Engineering", "description": "Creates features for model training", "status": "completed", "runtime": "00:18:20"},
                {"id": "model_training", "name": "Model Training", "description": "Trains prediction models", "status": "completed", "runtime": "01:24:56"},
                {"id": "model_validation", "name": "Model Validation", "description": "Validates models against test data", "status": "failed", "runtime": "00:05:23"},
                {"id": "model_deployment", "name": "Model Deployment", "description": "Deploys models to production", "status": "pending", "runtime": "00:00:00"}
            ],
            "lastRun": "2023-12-14T09:15:33",
            "nextScheduledRun": "2023-12-21T09:00:00",
            "averageRuntime": "02:01:24",
            "status": "failed"
        }
    }
    
    return pipelines

@router.get("/pipelines/{pipeline_id}", response_model=PipelineStatus)
async def get_pipeline(pipeline_id: str):
    """
    Get specific pipeline status
    """
    logger.info(f"Request for pipeline: {pipeline_id}")
    
    pipelines = await get_pipelines()
    
    if pipeline_id not in pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
    
    return pipelines[pipeline_id]

@router.get("/pipelines/{pipeline_id}/executions", response_model=List[PipelineExecution])
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

@router.get("/models/{model_name}/versions", response_model=List[ModelVersion])
async def get_model_versions(model_name: str):
    """
    Get all versions of a specific model
    """
    logger.info(f"Request for versions of model: {model_name}")
    
    # Check if model exists in registry
    registry_index_path = MODEL_REGISTRY_PATH / "registry_index.json"
    
    if registry_index_path.exists():
        with open(registry_index_path, "r") as f:
            registry_index = json.load(f)
            
        if model_name in registry_index.get("models", {}):
            # Get versions from registry
            versions = []
            for version_info in registry_index["models"][model_name]["versions"]:
                versions.append({
                    "id": version_info["version"],
                    "name": f"{model_name} v{version_info['version']}",
                    "date": version_info["created_at"],
                    "status": "production" if version_info["version"] == registry_index["models"][model_name].get("production_version") else "archived"
                })
            
            return versions
    
    # If no registry or model not in registry, return mock data
    return [
        {"id": "v1.0.2", "name": f"{model_name} v1.0.2", "date": "2023-12-15T14:30:22", "status": "production"},
        {"id": "v1.0.1", "name": f"{model_name} v1.0.1", "date": "2023-12-10T10:15:33", "status": "archived"},
        {"id": "v1.0.0", "name": f"{model_name} v1.0.0", "date": "2023-12-05T09:22:15", "status": "archived"}
    ]

@router.get("/models/{model_name}/metrics", response_model=ModelMetrics)
async def get_model_metrics(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version")
):
    """
    Get metrics for a specific model version
    """
    logger.info(f"Request for metrics of model: {model_name}, version: {version}")
    
    try:
        # Check if model exists in registry index
        registry_index_path = MODEL_REGISTRY_PATH / "registry_index.json"
        if registry_index_path.exists():
            with open(registry_index_path, "r") as f:
                registry_index = json.load(f)
            
            # If model exists in registry and version is not specified,
            # use the production version or latest version
            if model_name in registry_index.get("models", {}) and not version:
                versions = registry_index["models"][model_name]["versions"]
                if versions:
                    # Get the production version or the latest version
                    prod_version = registry_index["models"][model_name].get("production_version")
                    version = prod_version or versions[-1]["version"]
                    logger.info(f"Using version {version} for model {model_name}")
        
        # Look for evaluation results in different locations
        potential_paths = [
            MODEL_REGISTRY_PATH / model_name / (version or "latest") / "evaluation_results.json", 
            MODEL_REGISTRY_PATH / model_name / (version or "latest") / "model_evaluation.json",
            Path(f"models/registry/{model_name}/{version or 'latest'}/evaluation_results.json"),
            Path(f"results/{model_name}/{version or 'latest'}/evaluation.json")
        ]
        
        for eval_path in potential_paths:
            if eval_path.exists():
                logger.info(f"Found metrics at {eval_path}")
                with open(eval_path, "r") as f:
                    metrics = json.load(f)
                    # Ensure we have all required fields
                    required_fields = ["coherence_score", "diversity_score", "document_coverage", "total_documents"]
                    for field in required_fields:
                        if field not in metrics:
                            metrics[field] = 0.0 if field != "total_documents" else 0
                    return ModelMetrics(**metrics)
    except Exception as e:
        logger.warning(f"Error retrieving metrics for {model_name} v{version}: {str(e)}")
    
    # If we get here, we didn't find actual metrics, use mock data based on the model name
    mock_metrics = {
        "topic_model": {
            "coherence_score": 0.78,
            "diversity_score": 0.65,
            "document_coverage": 0.92,
            "total_documents": 15764,
            "uniqueness_score": 0.81,
            "silhouette_score": 0.72,
            "topic_separation": 0.68,
            "avg_topic_similarity": 0.43,
            "execution_time": 183.4,
            "topic_quality": 0.75
        },
        "sentiment_classifier": {
            "coherence_score": 0.82,
            "diversity_score": 0.70,
            "document_coverage": 0.95,
            "total_documents": 22345,
            "uniqueness_score": 0.76,
            "silhouette_score": 0.69,
            "topic_separation": 0.71,
            "avg_topic_similarity": 0.38,
            "execution_time": 205.2,
            "topic_quality": 0.82
        },
        "anomaly_detector": {
            "coherence_score": 0.74,
            "diversity_score": 0.68,
            "document_coverage": 0.88,
            "total_documents": 8932,
            "uniqueness_score": 0.77,
            "silhouette_score": 0.65,
            "topic_separation": 0.64,
            "avg_topic_similarity": 0.45,
            "execution_time": 142.7,
            "topic_quality": 0.72
        }
    }
    
    metrics_data = mock_metrics.get(model_name, mock_metrics["topic_model"])
    logger.info(f"Using mock metrics for {model_name} v{version}")
    return ModelMetrics(**metrics_data)

@router.get("/models/{model_name}/drift", response_model=DriftMetrics)
async def get_model_drift(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version")
):
    """
    Get data drift metrics for a specific model version
    """
    logger.info(f"MLOps API: Request for drift metrics of model: {model_name}, version: {version}")
    
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
        logger.error(f"Error reading drift metrics: {e}")
    
    # Return mock drift metrics if no actual metrics found
    result = DriftMetrics(
        timestamp=datetime.now().isoformat(),
        dataset_drift=True,
        share_of_drifted_columns=0.25,
        drifted_columns=["text_length", "sentiment_score", "engagement_rate"]
    )
    logger.info(f"Returning mock drift metrics: {result}")
    return result

@router.post("/pipelines/{pipeline_id}/execute")
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
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
    
    try:
        # Actually run the MLOpsPipeline instead of just returning a mock response
        model_name = pipeline_to_model[pipeline_id]
        execution_id = f"exec-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Execute the pipeline asynchronously without blocking the response
        def run_pipeline():
            try:
                results = run_mlops_pipeline(model_name, data_path="data/processed")
                logger.info(f"Pipeline {pipeline_id} execution complete with results: {results}")
                # Save results to the registry
                registry_dir = MODEL_REGISTRY_PATH / model_name / results.get("version", "latest")
                registry_dir.mkdir(parents=True, exist_ok=True)
                with open(registry_dir / "pipeline_results.json", "w") as f:
                    json.dump(results, f, indent=2)
            except Exception as e:
                logger.error(f"Error executing pipeline {pipeline_id}: {str(e)}")
        
        # Start the pipeline in a background thread
        import threading
        thread = threading.Thread(target=run_pipeline)
        thread.daemon = True
        thread.start()
        
        return {
            "execution_id": execution_id,
            "pipeline_id": pipeline_id,
            "status": "started",
            "startTime": datetime.now().isoformat(),
            "message": f"Pipeline {pipeline_id} execution started with ID {execution_id}"
        }
    except Exception as e:
        logger.error(f"Error initiating pipeline {pipeline_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing pipeline: {str(e)}") 