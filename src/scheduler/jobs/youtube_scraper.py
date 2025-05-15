import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
import pandas as pd
import os
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
import urllib.parse

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging setup with rotation
log_handler = RotatingFileHandler(
    LOG_DIR / "youtube.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=5
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger = logging.getLogger("youtube_scraper")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Also add console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger.addHandler(console_handler)

# Load environment variables
load_dotenv()

# YouTube API
API_KEY = os.getenv("YT_KEY")
if not API_KEY:
    logger.error("No YT_KEY found. Please check .env file.")
    raise EnvironmentError("YT_KEY missing")

youtube = build("youtube", "v3", developerKey=API_KEY)

def get_db_connection():
    # Parse the DATABASE_URL to modify the database name
    url = os.getenv("DATABASE_URL")
    result = urllib.parse.urlparse(url)
    
    # Create a new URL with the youtube_data database
    new_url = f"{result.scheme}://{result.username}:{result.password}@{result.hostname}:{result.port}/youtube_data"
    
    try:
        # First try to connect to youtube_data database
        conn = psycopg2.connect(new_url)
        conn.autocommit = True  # Set autocommit to True for table creation
        return conn
    except psycopg2.OperationalError:
        # If youtube_data doesn't exist, connect to the default database and create youtube_data
        with psycopg2.connect(url) as default_conn:
            default_conn.autocommit = True
            with default_conn.cursor() as cur:
                # Close existing connections to the database if it exists
                cur.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = 'youtube_data'
                    AND pid <> pg_backend_pid()
                """)
                # Drop database if it exists
                cur.execute("DROP DATABASE IF EXISTS youtube_data")
                # Create database
                cur.execute('CREATE DATABASE youtube_data')
        
        # Now connect to the new database
        conn = psycopg2.connect(new_url)
        conn.autocommit = True  # Set autocommit to True for table creation
        return conn

def should_scrape():
    """Check if enough time has passed since the last scrape"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Create table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS youtube_data (
                        video_id VARCHAR(50),
                        title TEXT,
                        description TEXT,
                        channel_title VARCHAR(255),
                        published_at TIMESTAMP,
                        view_count INTEGER,
                        like_count INTEGER,
                        comment_count INTEGER,
                        url TEXT,
                        scraped_at TIMESTAMP,
                        trending_date DATE,
                        PRIMARY KEY (video_id, trending_date)
                    )
                """)
                
                cur.execute("""
                    SELECT MAX(scraped_at) as last_scrape
                    FROM youtube_data
                """)
                result = cur.fetchone()
                
                if not result or not result[0]:
                    return True
                
                last_scrape = result[0]
                time_since_last = datetime.now() - last_scrape
                
                if time_since_last < timedelta(minutes=15):
                    logger.info(f"Last scrape was {time_since_last.total_seconds() / 60:.1f} minutes ago - waiting")
                    return False
                    
                return True
    except Exception as e:
        logger.warning(f"Error checking last scrape time: {e}")
        return True

def scrape_youtube_trending(region="DE", max_results=50):
    if not should_scrape():
        return
        
    try:
        logger.info(f"Starting YouTube scraping for region {region}...")

        request = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=region,
            maxResults=max_results
        )
        response = request.execute()
        logger.info("Successfully fetched trending videos from YouTube API")

        videos = []
        scrape_time = datetime.now()

        for item in response.get("items", []):
            snippet = item["snippet"]
            stats = item.get("statistics", {})

            videos.append({
                "video_id": item["id"],
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "url": f"https://www.youtube.com/watch?v={item['id']}",
                "scraped_at": scrape_time,
                "trending_date": scrape_time.date()
            })

        logger.info(f"Found {len(videos)} trending videos")

        if videos:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create table if it doesn't exist
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS youtube_data (
                            video_id VARCHAR(50),
                            title TEXT,
                            description TEXT,
                            channel_title VARCHAR(255),
                            published_at TIMESTAMP,
                            view_count INTEGER,
                            like_count INTEGER,
                            comment_count INTEGER,
                            url TEXT,
                            scraped_at TIMESTAMP,
                            trending_date DATE,
                            PRIMARY KEY (video_id, trending_date)
                        )
                    """)
                    
                    # Insert data
                    insert_query = """
                        INSERT INTO youtube_data (
                            video_id, title, description, channel_title,
                            published_at, view_count, like_count, comment_count,
                            url, scraped_at, trending_date
                        )
                        VALUES %s
                        ON CONFLICT (video_id, trending_date) 
                        DO UPDATE SET 
                            view_count = EXCLUDED.view_count,
                            like_count = EXCLUDED.like_count,
                            comment_count = EXCLUDED.comment_count,
                            scraped_at = EXCLUDED.scraped_at
                    """
                    
                    values = [(
                        video["video_id"],
                        video["title"],
                        video["description"],
                        video["channel_title"],
                        video["published_at"],
                        video["view_count"],
                        video["like_count"],
                        video["comment_count"],
                        video["url"],
                        video["scraped_at"],
                        video["trending_date"]
                    ) for video in videos]
                    
                    execute_values(cur, insert_query, values)
                    conn.commit()

            logger.info(f"Successfully stored {len(videos)} YouTube videos in the database")

    except Exception as e:
        logger.error(f"Error during YouTube scraping: {e}")
        logger.exception("Detailed error:")

if __name__ == "__main__":
    scrape_youtube_trending()
