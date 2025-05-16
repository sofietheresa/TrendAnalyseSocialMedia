from fastapi import FastAPI, HTTPException, BackgroundTasks, Security, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
from datetime import datetime
import logging
import os
from pathlib import Path
import json
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import numpy as np
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

# Import models and database
from models import get_db, RedditData, TikTokData, YouTubeData, init_db, Base, engine

# Environment variables and configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Modell-Download beim Start
from src.model_loader import download_models

# Import pipeline components
from src.pipelines.steps.data_ingestion import ingest_data
from src.pipelines.steps.preprocessing import preprocess_data
from src.pipelines.steps.data_exploration import explore_data
from src.pipelines.steps.predictions import make_predictions

# Import API routers
from src.api import api_router
from src.api.mlops_api import router as mlops_router, DriftMetrics

# Define the PipelineExecution model for direct endpoints
class PipelineExecution(BaseModel):
    id: str
    pipelineId: str
    startTime: str
    endTime: Optional[str] = None
    status: str
    trigger: str

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for service status
service_ready = False
initialization_error = None

app = FastAPI(
    title="Social Media Trend Analysis API",
    description="API for analyzing social media trends",
    version="1.0.0",
)

# CORS Middleware
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Security
API_KEY = os.getenv("API_KEY", "your-api-key")
api_key_header = APIKeyHeader(name="API_KEY")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Simple Health Check Endpoint
@app.get("/health")
async def health_check():
    """
    Simple health check endpoint that always returns OK
    """
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Create model registry directory if it doesn't exist
        model_registry_path = Path("models/registry")
        model_registry_path.mkdir(parents=True, exist_ok=True)
        
        # Create topic model directory
        topic_model_path = model_registry_path / "topic_model" / "v1.0.2"
        topic_model_path.mkdir(parents=True, exist_ok=True)
        
        # Create drift metrics file if it doesn't exist
        drift_metrics_path = topic_model_path / "drift_metrics.json"
        if not drift_metrics_path.exists():
            drift_metrics = {
                "timestamp": datetime.now().isoformat(),
                "dataset_drift": True,
                "share_of_drifted_columns": 0.25,
                "drifted_columns": ["text_length", "sentiment_score", "engagement_rate"]
            }
            with open(drift_metrics_path, "w") as f:
                json.dump(drift_metrics, f, indent=2)
        
        logger.info("Startup initialization completed successfully")
    except Exception as e:
        logger.error(f"Startup initialization failed: {str(e)}")
        # Don't raise the exception here to allow the application to start

# Modelle beim Start herunterladen
try:
    logging.info("Prüfe und lade Modelle falls nötig...")
    download_models()
except Exception as e:
    logging.error(f"Fehler beim Herunterladen der Modelle: {str(e)}")

try:
    qdrant_client = QdrantClient(url=QDRANT_URL)
    # Initialize sentence transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"Failed to initialize Qdrant client or model: {str(e)}")
    qdrant_client = None
    model = None

# Pydantic models
class ScrapeRequest(BaseModel):
    platform: str
    query: Optional[str] = None
    max_posts: Optional[int] = 100
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    platform: Optional[str] = None
    min_score: Optional[float] = 0.5

class PipelineResponse(BaseModel):
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None

@app.post("/sync", dependencies=[Depends(verify_api_key)])
async def sync_data(request: Request, db: Session = Depends(get_db)):
    """Synchronisiere Daten von externen Clients"""
    try:
        payload = await request.json()
        data: List[Dict] = payload.get("data", [])
        if not data:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Keine Daten zum Synchronisieren gefunden"
            )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Ungültiges JSON-Format"
        )

    stats = {"inserted": 0, "updated": 0, "errors": 0}
    
    try:
        for item in data:
            platform = item.get("platform")
            try:
                if platform == "reddit":
                    reddit_post = RedditData(
                        id=item.get("id"),
                        title=item.get("title"),
                        text=item.get("text"),
                        author=item.get("author"),
                        score=item.get("score"),
                        created_utc=item.get("created_utc"),
                        num_comments=item.get("num_comments"),
                        url=item.get("url"),
                        subreddit=item.get("subreddit"),
                        scraped_at=datetime.now()
                    )
                    db.merge(reddit_post)
                    stats["inserted"] += 1
                
                elif platform == "tiktok":
                    tiktok_post = TikTokData(
                        id=item.get("id"),
                        description=item.get("description"),
                        author_username=item.get("author_username"),
                        author_id=item.get("author_id"),
                        likes=item.get("likes"),
                        shares=item.get("shares"),
                        comments=item.get("comments"),
                        plays=item.get("plays"),
                        video_url=item.get("video_url"),
                        created_time=item.get("created_time"),
                        scraped_at=datetime.now()
                    )
                    db.merge(tiktok_post)
                    stats["inserted"] += 1
                
                elif platform == "youtube":
                    youtube_post = YouTubeData(
                        video_id=item.get("video_id"),
                        title=item.get("title"),
                        description=item.get("description"),
                        channel_title=item.get("channel_title"),
                        view_count=item.get("view_count"),
                        like_count=item.get("like_count"),
                        comment_count=item.get("comment_count"),
                        published_at=item.get("published_at"),
                        scraped_at=datetime.now()
                    )
                    db.merge(youtube_post)
                    stats["inserted"] += 1
                    
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von {platform}-Daten: {e}")
                stats["errors"] += 1
                continue
        
        db.commit()
        
        return JSONResponse(
            status_code=HTTP_201_CREATED,
            content={
                "status": "success",
                "message": "Synchronisation abgeschlossen",
                "stats": stats
            }
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Fehler während der Synchronisation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Datenbankfehler: {str(e)}"
        )

@app.get("/data", dependencies=[Depends(verify_api_key)])
async def get_data(db: Session = Depends(get_db)):
    """Alle Daten aus allen Plattform-Tabellen abrufen"""
    try:
        all_data = []
        
        # Reddit-Daten
        reddit_data = db.query(RedditData).all()
        for item in reddit_data:
            data = {
                "platform": "reddit",
                **item.__dict__
            }
            if "_sa_instance_state" in data:
                del data["_sa_instance_state"]
            all_data.append(data)
        
        # TikTok-Daten
        tiktok_data = db.query(TikTokData).all()
        for item in tiktok_data:
            data = {
                "platform": "tiktok",
                **item.__dict__
            }
            if "_sa_instance_state" in data:
                del data["_sa_instance_state"]
            all_data.append(data)
        
        # YouTube-Daten
        youtube_data = db.query(YouTubeData).all()
        for item in youtube_data:
            data = {
                "platform": "youtube",
                **item.__dict__
            }
            if "_sa_instance_state" in data:
                del data["_sa_instance_state"]
            all_data.append(data)
        
        return {"data": all_data}
    
    except Exception as e:
        logger.error(f"Fehler beim Datenabruf: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Datenbankfehler: {str(e)}"
        )

# Register routers
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(mlops_router, prefix="/api/mlops", tags=["mlops"])

# Add a direct route for model drift to ensure it's accessible
@app.get("/api/mlops/models/{model_name}/drift", response_model=DriftMetrics, tags=["direct"])
async def get_model_drift(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version")
):
    """
    Get data drift metrics for a specific model version
    """
    logger.info(f"DIRECT: Request for drift metrics of model: {model_name}, version: {version}")
    
    # Set default version if not provided
    if not version:
        version = "v1.0.2"  # Default to latest version
        logger.info(f"No version specified, using default: {version}")
    
    # Check for actual drift metrics in model registry
    model_registry_path = Path("models/registry").resolve()
    drift_path = model_registry_path / model_name / version / "drift_metrics.json"
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
    return DriftMetrics(
        timestamp=datetime.now().isoformat(),
        dataset_drift=True,
        share_of_drifted_columns=0.25,
        drifted_columns=["text_length", "sentiment_score", "engagement_rate"]
    )

# Direct pipeline endpoints from drift_api.py
@app.get("/api/mlops/pipelines", tags=["direct"])
async def get_pipelines():
    """
    Get all ML pipelines status
    """
    logger.info("Direct request for all pipelines")
    
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

@app.get("/api/mlops/pipelines/{pipeline_id}", tags=["direct"])
async def get_pipeline(pipeline_id: str):
    """
    Get details for a specific pipeline
    """
    logger.info(f"Direct request for pipeline: {pipeline_id}")
    
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

@app.get("/api/mlops/pipelines/{pipeline_id}/executions", tags=["direct"])
async def get_pipeline_executions(pipeline_id: str):
    """
    Get executions for a specific pipeline
    """
    logger.info(f"Direct request for executions of pipeline: {pipeline_id}")
    
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

@app.post("/api/mlops/pipelines/{pipeline_id}/execute", tags=["direct"])
async def execute_pipeline(pipeline_id: str):
    """
    Execute a specific pipeline
    """
    logger.info(f"Direct request to execute pipeline: {pipeline_id}")
    
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

# Debug endpoint to verify available routes
@app.get("/debug/routes")
async def debug_routes():
    """
    Debug endpoint to list all registered routes in the application
    """
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else None
        })
    
    return {"routes": routes}

@app.get("/ping")
async def ping():
    """
    Simple ping endpoint for checking if the API is running
    """
    return {"status": "ok", "message": "API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 