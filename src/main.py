from fastapi import FastAPI, HTTPException, BackgroundTasks, Security, Depends, Request
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

# Modell-Download beim Start
from src.model_loader import download_models

# Import pipeline components
from src.pipelines.steps.data_ingestion import ingest_data
from src.pipelines.steps.preprocessing import preprocess_data
from src.pipelines.steps.data_exploration import explore_data
from src.pipelines.steps.predictions import make_predictions

# Import API routers
from src.api import api_router
from src.api.mlops_api import router as mlops_router

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
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
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
        await initialize_services()
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 