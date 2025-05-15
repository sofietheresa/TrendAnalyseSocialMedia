from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta
import urllib.parse
import logging
import sys
import traceback
import time
import uvicorn

# Enhanced logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Log environment variables (excluding sensitive ones)
logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
logger.info(f"Port: {os.getenv('PORT', '8080')}")

app = FastAPI(
    title="TrendAnalyseSocialMedia API",
    description="API for analyzing social media trends",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React Dev Server
        "https://trendanalysesocialmedia.vercel.app",  # Produktions-URL
        "https://trendanalysesocialmedia-production.up.railway.app"  # Railway App URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request started: {request.method} {request.url.path} ({request.client.host if request.client else 'unknown'})")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.2f}s")
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - Error: {str(e)}")
        logger.error(traceback.format_exc())
        process_time = time.time() - start_time
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "traceback": traceback.format_exc(),
                "duration": f"{process_time:.2f}s"
            }
        )

# Database connection
db_engine = None

def get_db_connection():
    """Get a database connection with retry logic"""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            global db_engine
            if db_engine is not None:
                # Test if the connection is still valid
                with db_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    logger.debug("Reusing existing database connection")
                return db_engine

            url = os.getenv("DATABASE_URL")
            logger.info(f"Connecting to database (attempt {attempt+1}/{max_retries})")
            
            if not url:
                logger.error("DATABASE_URL environment variable is not set")
                raise ValueError("DATABASE_URL environment variable is not set")
            
            # Configure SQLAlchemy engine with connection pooling and timeouts
            db_engine = create_engine(
                url,
                pool_size=5,  # Reduced pool size
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,  # Recycle connections after 30 minutes
                connect_args={
                    "connect_timeout": 10,  # Connection timeout in seconds
                    "application_name": "trendanalyse-api"  # Identify app in pg_stat_activity
                }
            )
            
            # Test the connection
            with db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                one = result.scalar()
                if one != 1:
                    raise Exception(f"Database test query returned {one} instead of 1")
                logger.info("Successfully connected to database")
            
            return db_engine
            
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection failed (attempt {attempt+1}/{max_retries}): {str(e)}")
                logger.warning(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                # Clear the engine in case it's in a bad state
                db_engine = None
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {str(e)}")
                logger.error(traceback.format_exc())
                raise

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "TrendAnalyseSocialMedia API is running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    health_status = {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "application": "healthy",
            "database": "unknown"
        }
    }
    
    try:
        db = get_db_connection()
        with db.connect() as conn:
            conn.execute(text("SELECT 1"))
            health_status["components"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        logger.error(traceback.format_exc())
        health_status["components"]["database"] = "unhealthy"
        health_status["database_error"] = str(e)
    
    return health_status

@app.get("/api/scraper-status")
async def get_scraper_status():
    try:
        logger.info("Fetching scraper status")
        db = get_db_connection()
            
        cutoff_time = datetime.now() - timedelta(minutes=20)
        
        status = {
            'reddit': {'running': False, 'total_posts': 0, 'last_update': None},
            'tiktok': {'running': False, 'total_posts': 0, 'last_update': None},
            'youtube': {'running': False, 'total_posts': 0, 'last_update': None}
        }
        
        # List of tables to check
        tables = [
            ('reddit_posts', 'reddit'),
            ('tiktok_posts', 'tiktok'),
            ('youtube_posts', 'youtube')
        ]
        
        with db.connect() as conn:
            # Check if tables exist first
            existing_tables = []
            try:
                # Use information_schema to check for table existence
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('reddit_posts', 'tiktok_posts', 'youtube_posts')
                """))
                existing_tables = [row[0] for row in result]
                logger.info(f"Found tables: {existing_tables}")
            except Exception as e:
                logger.error(f"Error checking table existence: {str(e)}")
            
            # Check each platform's data
            for table_name, platform in tables:
                try:
                    if table_name not in existing_tables:
                        logger.warning(f"Table {table_name} does not exist")
                        continue
                        
                    result = conn.execute(text(f"SELECT COUNT(*), MAX(scraped_at) FROM {table_name}"))
                    count, last_update = result.fetchone()
                    status[platform].update({
                        'running': last_update and last_update > cutoff_time,
                        'total_posts': count,
                        'last_update': last_update.isoformat() if last_update else None
                    })
                    logger.info(f"{platform.capitalize()} status updated: {status[platform]}")
                except Exception as e:
                    logger.error(f"Error fetching {platform} status: {str(e)}")
                    # Continue with other tables rather than failing completely
        
        return status
    except Exception as e:
        logger.error(f"Error in scraper status: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/daily-stats")
async def get_daily_stats():
    try:
        logger.info("Fetching daily stats")
        db = get_db_connection()
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        stats = {
            'reddit': [],
            'tiktok': [],
            'youtube': []
        }
        
        # List of tables to check
        tables = [
            ('reddit_posts', 'reddit'),
            ('tiktok_posts', 'tiktok'),
            ('youtube_posts', 'youtube')
        ]
        
        with db.connect() as conn:
            # Check if tables exist first
            existing_tables = []
            try:
                # Use information_schema to check for table existence
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('reddit_posts', 'tiktok_posts', 'youtube_posts')
                """))
                existing_tables = [row[0] for row in result]
                logger.info(f"Found tables: {existing_tables}")
            except Exception as e:
                logger.error(f"Error checking table existence: {str(e)}")
            
            # Check each platform's data
            for table_name, platform in tables:
                try:
                    if table_name not in existing_tables:
                        logger.warning(f"Table {table_name} does not exist")
                        continue
                        
                    query = text(f"""
                        SELECT DATE(scraped_at) as date, COUNT(*) as count
                        FROM {table_name}
                        WHERE scraped_at >= :start_date
                        GROUP BY DATE(scraped_at)
                        ORDER BY date
                    """)
                    
                    result = conn.execute(query, {'start_date': start_date})
                    stats[platform] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
                    logger.info(f"{platform.capitalize()} stats fetched: {len(stats[platform])} days of data")
                except Exception as e:
                    logger.error(f"Error fetching {platform} daily stats: {str(e)}")
                    # Continue with other tables rather than failing completely
        
        return stats
    except Exception as e:
        logger.error(f"Error in daily stats: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting application on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info") 