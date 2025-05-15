import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
import os
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values

# Load environment variables
load_dotenv()

# Setup paths and logging
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logger with file and console handlers
logger = logging.getLogger("youtube_scraper")
logger.setLevel(logging.INFO)

# File handler with rotation
log_handler = RotatingFileHandler(
    LOG_DIR / "youtube.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=5
)
log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(log_handler)

# Console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

# Initialize YouTube API
API_KEY = os.getenv("YT_KEY")
if not API_KEY:
    error_msg = "No YT_KEY found. Please check .env file."
    logger.error(error_msg)
    raise EnvironmentError("YT_KEY missing")

youtube = build("youtube", "v3", developerKey=API_KEY)

def get_db_connection():
    """Create a connection to the database specified in DATABASE_URL"""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def should_scrape():
    """Check if enough time has passed since the last scrape (6 hours)"""
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
                
                cur.execute("SELECT MAX(scraped_at) as last_scrape FROM public.youtube_data")
                result = cur.fetchone()
                
                if not result or not result[0]:
                    return True
                
                last_scrape = result[0]
                time_since_last = datetime.now() - last_scrape
                
                # Return True if it's been more than 6 hours since last scrape
                return time_since_last > timedelta(hours=6)
    except Exception as e:
        logger.warning(f"Error checking last scrape time: {e}")
        return True

def update_status(error_message=None):
    """Update YouTube scraper status in the database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                now = datetime.now()
                today = now.date()
                
                description = f"YouTube API Error: {error_message}" if error_message else "YouTube Status Update"
                
                cur.execute("""
                    INSERT INTO public.youtube_data 
                    (video_id, title, description, channel_title, published_at, view_count, like_count, comment_count, url, scraped_at, trending_date)
                    VALUES ('status_update', 'Status Update', %s, 'Scraper', %s, 0, 0, 0, 'https://example.com', %s, %s)
                    ON CONFLICT (video_id, trending_date) DO UPDATE SET 
                        description = EXCLUDED.description,
                        scraped_at = EXCLUDED.scraped_at
                """, (description, now, now, today))
                conn.commit()
                logger.info("YouTube status updated in database")
                return True
    except Exception as e:
        logger.error(f"Error updating YouTube status: {str(e)}")
        return False

def scrape_youtube_trending(region="DE", max_results=50):
    """
    Scrape trending videos from YouTube and store in the database
    
    Args:
        region: Country code for region-specific trends (default: DE)
        max_results: Maximum number of videos to fetch (default: 50)
    """
    # Check if we should run scraping now
    should_run = should_scrape()
    if not should_run:
        logger.info("Skipping scrape - not enough time has passed since last scrape")
        update_status()
        return
    
    logger.info(f"Starting YouTube scraping for region {region}, looking for {max_results} videos...")
        
    try:
        # Fetch videos from YouTube API
        try:
            request = youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region,
                maxResults=max_results
            )
            response = request.execute()
            logger.info("Successfully fetched trending videos from YouTube API")
        except Exception as e:
            error_msg = f"Error fetching trending videos from YouTube API: {str(e)}"
            logger.error(error_msg)
            update_status(str(e))
            return

        # Process video data
        videos = []
        scrape_time = datetime.now()
        today_date = scrape_time.date()

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
                "trending_date": today_date
            })

        video_count = len(videos)
        logger.info(f"Found {video_count} trending videos")

        # Store videos in database
        if videos:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create table if it doesn't exist (redundant but safe)
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
                    
                    # Get count before insertion
                    cur.execute("SELECT COUNT(*) FROM youtube_data WHERE trending_date = %s", (today_date,))
                    count_before = cur.fetchone()[0]
                    
                    # Insert data with conflict handling
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
                    
                    # Get count after insertion
                    cur.execute("SELECT COUNT(*) FROM youtube_data WHERE trending_date = %s", (today_date,))
                    count_after = cur.fetchone()[0]
                    
                    # Calculate new insertions
                    new_videos = count_after - count_before
                    updated_videos = video_count - new_videos
                    
                    conn.commit()
                    
                    logger.info(f"Inserted {new_videos} new videos and updated {updated_videos} existing videos in the database")

            logger.info(f"Successfully stored {video_count} YouTube videos in the database")

    except Exception as e:
        error_msg = f"Error during YouTube scraping: {e}"
        logger.error(error_msg)
        logger.exception("Detailed error:")
        # Update status on errors
        update_status(str(e))

if __name__ == "__main__":
    scrape_youtube_trending()
