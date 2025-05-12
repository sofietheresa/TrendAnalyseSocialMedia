from fastapi import FastAPI, Depends, HTTPException, Security
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from starlette.status import HTTP_403_FORBIDDEN
from dotenv import load_dotenv
import os
import sqlite3
from typing import List, Dict
import json
import time

# Load environment variables
load_dotenv()

app = FastAPI()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

SCRAPING_SUCCESS = Counter(
    'scraping_success_total',
    'Successful scraping operations',
    ['platform']
)

# API Key configuration
API_KEY = os.getenv("API_KEY", "your_secure_api_key_here")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/social_media.db")

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate API key"
    )

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE_URL.replace("sqlite:///", ""))
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    # Record request duration
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)
    
    # Record request count
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    return {"message": "Social Media Analysis API"}

@app.get("/api/data/reddit", dependencies=[Depends(get_api_key)])
async def get_reddit_data():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reddit_data ORDER BY created_utc DESC LIMIT 100")
        data = [dict(row) for row in cursor.fetchall()]
        return {"data": data}
    finally:
        conn.close()

@app.get("/api/data/tiktok", dependencies=[Depends(get_api_key)])
async def get_tiktok_data():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tiktok_data ORDER BY created_time DESC LIMIT 100")
        data = [dict(row) for row in cursor.fetchall()]
        return {"data": data}
    finally:
        conn.close()

@app.get("/api/data/youtube", dependencies=[Depends(get_api_key)])
async def get_youtube_data():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM youtube_data ORDER BY published_at DESC LIMIT 100")
        data = [dict(row) for row in cursor.fetchall()]
        return {"data": data}
    finally:
        conn.close()

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# ... existing code ... 