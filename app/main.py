from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta
import urllib.parse
import logging
import sys
import traceback

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

app = Flask(__name__)

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",  # React Dev Server
            "https://trendanalysesocialmedia.vercel.app",  # Produktions-URL
            "https://trendanalysesocialmedia-production.up.railway.app"  # Railway App URL
        ]
    }
})

# Optimize Flask app configuration
app.config.update(
    JSONIFY_PRETTYPRINT_REGULAR=False,  # Disable pretty printing of JSON
    JSON_SORT_KEYS=False,  # Disable JSON key sorting
    PROPAGATE_EXCEPTIONS=True  # Better error handling
)

# Single database engine with connection pooling configuration
db_engine = None

def get_db_connection():
    try:
        global db_engine
        if db_engine is not None:
            return db_engine

        url = os.getenv("DATABASE_URL")
        logger.info("Attempting to connect to database")
        
        if not url:
            logger.error("DATABASE_URL environment variable is not set")
            raise ValueError("DATABASE_URL environment variable is not set")
        
        # Configure SQLAlchemy engine with connection pooling
        db_engine = create_engine(
            url,
            pool_size=5,  # Reduced pool size
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800  # Recycle connections after 30 minutes
        )
        
        # Test the connection
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to database")
        
        return db_engine
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.route('/')
def root():
    return jsonify({
        "status": "online",
        "message": "TrendAnalyseSocialMedia API is running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    health_status = {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "application": "healthy",
            "database": "unknown"
        }
    }
    
    try:
        global db_engine
        if db_engine is None:
            db_engine = get_db_connection()
        
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            health_status["components"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        logger.error(traceback.format_exc())
        health_status["components"]["database"] = "unhealthy"
        health_status["database_error"] = str(e)
    
    # If database is unhealthy but application is running, we still return 200
    # but include the error details
    return jsonify(health_status)

@app.route('/api/scraper-status')
def get_scraper_status():
    try:
        logger.info("Fetching scraper status")
        global db_engine
        if db_engine is None:
            db_engine = get_db_connection()
            
        cutoff_time = datetime.now() - timedelta(minutes=20)
        
        status = {
            'reddit': {'running': False, 'total_posts': 0, 'last_update': None},
            'tiktok': {'running': False, 'total_posts': 0, 'last_update': None},
            'youtube': {'running': False, 'total_posts': 0, 'last_update': None}
        }
        
        with db_engine.connect() as conn:
            # Check Reddit
            result = conn.execute(text("SELECT COUNT(*), MAX(scraped_at) FROM reddit_posts"))
            count, last_update = result.fetchone()
            status['reddit'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
            logger.info(f"Reddit status updated: {status['reddit']}")
            
            # Check TikTok
            result = conn.execute(text("SELECT COUNT(*), MAX(scraped_at) FROM tiktok_posts"))
            count, last_update = result.fetchone()
            status['tiktok'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
            logger.info(f"TikTok status updated: {status['tiktok']}")
            
            # Check YouTube
            result = conn.execute(text("SELECT COUNT(*), MAX(scraped_at) FROM youtube_posts"))
            count, last_update = result.fetchone()
            status['youtube'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
            logger.info(f"YouTube status updated: {status['youtube']}")
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in scraper status: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/daily-stats')
def get_daily_stats():
    try:
        logger.info("Fetching daily stats")
        global db_engine
        if db_engine is None:
            db_engine = get_db_connection()
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        stats = {
            'reddit': [],
            'tiktok': [],
            'youtube': []
        }
        
        with db_engine.connect() as conn:
            # Get Reddit daily stats
            result = conn.execute(text("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM reddit_posts
                WHERE scraped_at >= :start_date
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """), {'start_date': start_date})
            stats['reddit'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
            logger.info(f"Reddit stats fetched: {len(stats['reddit'])} days of data")
            
            # Get TikTok daily stats
            result = conn.execute(text("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM tiktok_posts
                WHERE scraped_at >= :start_date
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """), {'start_date': start_date})
            stats['tiktok'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
            logger.info(f"TikTok stats fetched: {len(stats['tiktok'])} days of data")
            
            # Get YouTube daily stats
            result = conn.execute(text("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM youtube_posts
                WHERE scraped_at >= :start_date
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """), {'start_date': start_date})
            stats['youtube'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
            logger.info(f"YouTube stats fetched: {len(stats['youtube'])} days of data")
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in daily stats: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting application on port {port}")
    app.run(host='0.0.0.0', port=port) 