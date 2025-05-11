from fastapi import FastAPI, HTTPException, BackgroundTasks
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

# Import pipeline components
from src.pipelines.steps.data_ingestion import ingest_data
from src.pipelines.steps.preprocessing import preprocess_data
from src.pipelines.steps.data_exploration import explore_data
from src.pipelines.steps.predictions import make_predictions

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Qdrant client
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "social_media_posts"
EMBEDDING_SIZE = 768  # Default for many transformer models

try:
    qdrant_client = QdrantClient(url=QDRANT_URL)
    # Initialize sentence transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"Failed to initialize Qdrant client or model: {str(e)}")
    qdrant_client = None
    model = None

# Global state for tracking pipeline runs
pipeline_runs = {}

app = FastAPI(
    title="Social Media Analysis API",
    description="API for analyzing social media trends across different platforms",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
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
    run_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

def initialize_qdrant_collection():
    """Initialize Qdrant collection if it doesn't exist."""
    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if COLLECTION_NAME not in collection_names:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_SIZE,
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Created new collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {str(e)}")
        raise

def store_posts_in_qdrant(posts: List[Dict[str, Any]]):
    """Store posts in Qdrant with their embeddings."""
    try:
        if not qdrant_client or not model:
            raise ValueError("Qdrant client or model not initialized")

        # Generate embeddings for all posts
        texts = [post.get('text', '') for post in posts]
        embeddings = model.encode(texts)

        # Prepare points for Qdrant
        points = []
        for i, post in enumerate(posts):
            points.append(models.PointStruct(
                id=i,
                vector=embeddings[i].tolist(),
                payload={
                    'platform': post.get('platform'),
                    'text': post.get('text'),
                    'timestamp': post.get('timestamp'),
                    'engagement': post.get('engagement'),
                    'sentiment_score': post.get('sentiment_score')
                }
            ))

        # Upload points to Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        logger.info(f"Stored {len(points)} posts in Qdrant")
    except Exception as e:
        logger.error(f"Failed to store posts in Qdrant: {str(e)}")
        raise

# Background task to run pipeline steps
async def run_pipeline_step(step_name: str, data: Optional[Dict[str, Any]] = None):
    try:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        pipeline_runs[run_id] = {
            "status": "running",
            "step": step_name,
            "start_time": datetime.now().isoformat(),
            "error": None
        }

        if step_name == "scrape":
            # Implement scraping logic here
            pass
        elif step_name == "preprocess":
            raw_data = ingest_data()
            processed_data = preprocess_data(raw_data)
            
            # Store processed data in Qdrant
            if qdrant_client and model:
                store_posts_in_qdrant(processed_data.to_dict('records'))
            
            pipeline_runs[run_id]["status"] = "completed"
            pipeline_runs[run_id]["end_time"] = datetime.now().isoformat()
            return processed_data
        elif step_name == "explore":
            raw_data = ingest_data()
            processed_data = preprocess_data(raw_data)
            exploration_results = explore_data(processed_data)
            pipeline_runs[run_id]["status"] = "completed"
            pipeline_runs[run_id]["end_time"] = datetime.now().isoformat()
            return exploration_results
        elif step_name == "predict":
            raw_data = ingest_data()
            processed_data = preprocess_data(raw_data)
            exploration_results = explore_data(processed_data)
            predictions = make_predictions(processed_data, exploration_results)
            pipeline_runs[run_id]["status"] = "completed"
            pipeline_runs[run_id]["end_time"] = datetime.now().isoformat()
            return predictions
    except Exception as e:
        logger.error(f"Error in pipeline step {step_name}: {str(e)}")
        pipeline_runs[run_id]["status"] = "failed"
        pipeline_runs[run_id]["error"] = str(e)
        pipeline_runs[run_id]["end_time"] = datetime.now().isoformat()
        raise

@app.get("/")
async def root():
    """Root endpoint providing API overview."""
    return {
        "name": "Social Media Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "scrape": "/api/scrape",
            "download": "/api/download/{platform}",
            "preprocess": "/api/preprocess",
            "explore": "/api/explore",
            "predict": "/api/predict",
            "status": "/api/status/{run_id}",
            "search": "/api/search"
        },
        "documentation": "/docs"
    }

@app.post("/api/scrape", response_model=PipelineResponse)
async def scrape_data(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Scrape data from specified social media platform."""
    try:
        # Validate platform
        valid_platforms = ["tiktok", "youtube", "reddit"]
        if request.platform.lower() not in valid_platforms:
            raise HTTPException(status_code=400, detail=f"Invalid platform. Must be one of {valid_platforms}")
        
        # Add scraping task to background tasks
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        background_tasks.add_task(run_pipeline_step, "scrape", request.dict())
        
        return PipelineResponse(
            status="success",
            message=f"Started scraping {request.platform} data",
            run_id=run_id
        )
    except Exception as e:
        logger.error(f"Error in scrape endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{platform}", response_model=PipelineResponse)
async def download_data(platform: str):
    """Download previously scraped data for a specific platform."""
    try:
        data_dir = Path("data/raw")
        if not data_dir.exists():
            raise HTTPException(status_code=404, detail="No data directory found")
        
        platform_file = data_dir / f"{platform}_data.csv"
        if not platform_file.exists():
            raise HTTPException(status_code=404, detail=f"No data found for platform: {platform}")
        
        return PipelineResponse(
            status="success",
            message=f"Data for {platform} is available at {platform_file}",
            results={"file_path": str(platform_file)}
        )
    except Exception as e:
        logger.error(f"Error in download endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/preprocess", response_model=PipelineResponse)
async def preprocess_data_endpoint(background_tasks: BackgroundTasks):
    """Preprocess the raw data."""
    try:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        background_tasks.add_task(run_pipeline_step, "preprocess")
        return PipelineResponse(
            status="success",
            message="Started data preprocessing",
            run_id=run_id
        )
    except Exception as e:
        logger.error(f"Error in preprocess endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/explore", response_model=PipelineResponse)
async def explore_data_endpoint():
    """Get exploration results."""
    try:
        results_file = Path("data/processed/exploration_results.json")
        if not results_file.exists():
            raise HTTPException(status_code=404, detail="No exploration results found")
        
        # Read and return the actual results
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        return PipelineResponse(
            status="success",
            message="Exploration results retrieved successfully",
            results=results
        )
    except Exception as e:
        logger.error(f"Error in explore endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict", response_model=PipelineResponse)
async def predict_endpoint(background_tasks: BackgroundTasks):
    """Run predictions on the processed data."""
    try:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        background_tasks.add_task(run_pipeline_step, "predict")
        return PipelineResponse(
            status="success",
            message="Started prediction process",
            run_id=run_id
        )
    except Exception as e:
        logger.error(f"Error in predict endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{run_id}", response_model=PipelineResponse)
async def get_status(run_id: str):
    """Get the status of a pipeline run."""
    try:
        if run_id not in pipeline_runs:
            raise HTTPException(status_code=404, detail=f"No run found with ID: {run_id}")
        
        run_info = pipeline_runs[run_id]
        return PipelineResponse(
            status="success",
            message=f"Status for run {run_id}",
            results=run_info
        )
    except Exception as e:
        logger.error(f"Error in status endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search", response_model=PipelineResponse)
async def semantic_search(request: SearchRequest):
    """Perform semantic search on stored posts."""
    try:
        if not qdrant_client or not model:
            raise HTTPException(status_code=500, detail="Qdrant client or model not initialized")

        # Generate query embedding
        query_embedding = model.encode(request.query)

        # Prepare search parameters
        search_params = {
            "query_vector": query_embedding.tolist(),
            "limit": request.limit,
            "score_threshold": request.min_score
        }

        # Add platform filter if specified
        if request.platform:
            search_params["query_filter"] = models.Filter(
                must=[
                    models.FieldCondition(
                        key="platform",
                        match=models.MatchValue(value=request.platform)
                    )
                ]
            )

        # Perform search
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            **search_params
        )

        # Format results
        results = []
        for hit in search_results:
            results.append({
                "score": hit.score,
                "text": hit.payload.get("text"),
                "platform": hit.payload.get("platform"),
                "timestamp": hit.payload.get("timestamp"),
                "engagement": hit.payload.get("engagement"),
                "sentiment_score": hit.payload.get("sentiment_score")
            })

        return PipelineResponse(
            status="success",
            message=f"Found {len(results)} matching posts",
            results={"matches": results}
        )
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data")
async def get_data():
    data_dir = Path("data/raw")
    if not data_dir.exists():
        raise HTTPException(status_code=404, detail="Data directory not found")
    
    # Logic to retrieve and return data
    return JSONResponse(content={"message": "Data retrieved successfully"})

@app.get("/logs")
async def get_logs():
    logs_dir = Path("logs")
    if not logs_dir.exists():
        raise HTTPException(status_code=404, detail="Logs directory not found")
    
    # Logic to retrieve and return logs
    return JSONResponse(content={"message": "Logs retrieved successfully"})

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global exception handler for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )

if __name__ == "__main__":
    # Initialize Qdrant collection on startup
    if qdrant_client:
        initialize_qdrant_collection()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 