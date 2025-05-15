import asyncio
import os
import logging
from logging.handlers import RotatingFileHandler
from TikTokApi import TikTokApi
from dotenv import load_dotenv
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
import urllib.parse
from datetime import datetime
import traceback

load_dotenv()

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging setup with rotation
log_handler = RotatingFileHandler(
    LOG_DIR / "tiktok.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=5
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger = logging.getLogger("tiktok_scraper")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Also add console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger.addHandler(console_handler)

def get_db_connection():
    """
    Create a connection to the main database specified in DATABASE_URL
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        # Connect directly to the main database (railway)
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

async def trending_videos():
    ms_token = os.getenv("MS_TOKEN")
    if not ms_token:
        logger.error("MS_TOKEN missing. Please check your .env file.")
        return

    browser = os.getenv("TIKTOK_BROWSER", "chromium")
    logger.info(f"Using browser: {browser}")
    
    api = None
    try:
        api = TikTokApi()
        logger.info("Creating TikTok API session...")
        
        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=3,
            browser=browser,
            headless=True
        )
        logger.info("TikTok API session created successfully")

        data = []
        seen_video_ids = set()  # Track unique video IDs
        logger.info("Loading trending videos from TikTok...")

        video_count = 0
        async for video in api.trending.videos(count=30):
            try:
                info = video.as_dict
                video_id = info.get("id")
                
                # Skip if we've already seen this video in this batch
                if video_id in seen_video_ids:
                    logger.debug(f"Skipping duplicate video: {video_id}")
                    continue
                    
                seen_video_ids.add(video_id)
                video_count += 1
                logger.debug(f"Processing video {video_count}: {video_id}")
                
                data.append({
                    "id": video_id,
                    "description": info.get("desc"),
                    "author_username": info.get("author", {}).get("uniqueId"),
                    "author_id": info.get("author", {}).get("id"),
                    "likes": info.get("stats", {}).get("diggCount"),
                    "shares": info.get("stats", {}).get("shareCount"),
                    "comments": info.get("stats", {}).get("commentCount"),
                    "plays": info.get("stats", {}).get("playCount"),
                    "video_url": info.get("video", {}).get("downloadAddr"),
                    "created_time": info.get("createTime"),
                    "scraped_at": datetime.now()
                })
            except Exception as e:
                logger.error(f"Error processing video: {str(e)}")
                logger.debug(traceback.format_exc())
                continue

        if not data:
            logger.warning("No videos found.")
            return

        logger.info(f"Found {len(data)} unique videos, attempting to store in database...")

        # Store in PostgreSQL
        if data:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create table if it doesn't exist
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS public.tiktok_data (
                            id VARCHAR(50),
                            description TEXT,
                            author_username VARCHAR(100),
                            author_id VARCHAR(50),
                            likes INTEGER,
                            shares INTEGER,
                            comments INTEGER,
                            plays INTEGER,
                            video_url TEXT,
                            created_time BIGINT,
                            scraped_at TIMESTAMP,
                            PRIMARY KEY (id)
                        )
                    """)
                    
                    # Insert data one by one to handle duplicates better
                    inserted = 0
                    updated = 0
                    for post in data:
                        try:
                            # Try to insert
                            cur.execute("""
                                INSERT INTO public.tiktok_data (
                                    id, description, author_username, author_id,
                                    likes, shares, comments, plays, video_url,
                                    created_time, scraped_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (id) 
                                DO UPDATE SET 
                                    likes = EXCLUDED.likes,
                                    shares = EXCLUDED.shares,
                                    comments = EXCLUDED.comments,
                                    plays = EXCLUDED.plays,
                                    scraped_at = EXCLUDED.scraped_at
                                RETURNING (xmax = 0) AS inserted
                            """, (
                                post["id"],
                                post["description"],
                                post["author_username"],
                                post["author_id"],
                                post["likes"],
                                post["shares"],
                                post["comments"],
                                post["plays"],
                                post["video_url"],
                                post["created_time"],
                                post["scraped_at"]
                            ))
                            
                            # Check if it was an insert or update
                            result = cur.fetchone()
                            if result[0]:
                                inserted += 1
                            else:
                                updated += 1
                                
                        except Exception as e:
                            logger.error(f"Error inserting video {post['id']}: {str(e)}")
                            continue
                    
                    conn.commit()
                    logger.info(f"Successfully processed {len(data)} videos ({inserted} inserted, {updated} updated)")

    except Exception as e:
        logger.error(f"Error during TikTok scraping: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())

    finally:
        try:
            if api and hasattr(api, "browser") and api.browser:
                logger.info("Closing browser session...")
                await api.stop_playwright()
                logger.info("Browser session closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

if __name__ == "__main__":
    asyncio.run(trending_videos())