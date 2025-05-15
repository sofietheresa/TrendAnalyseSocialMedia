import os
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import psycopg2
import urllib.parse
from pathlib import Path
from jobs.reddit_scraper import scrape_reddit
from jobs.tiktok_scraper import trending_videos as scrape_tiktok
from jobs.youtube_scraper import scrape_youtube_trending

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging setup with rotation
log_handler = RotatingFileHandler(
    LOG_DIR / "scraper.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=5
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger = logging.getLogger("main_scraper")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Also add console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger.addHandler(console_handler)

def get_db_connection(db_name):
    url = os.getenv("DATABASE_URL")
    result = urllib.parse.urlparse(url)
    new_url = f"{result.scheme}://{result.username}:{result.password}@{result.hostname}:{result.port}/{db_name}"
    return psycopg2.connect(new_url)

def get_table_count(db_name, table_name):
    try:
        with get_db_connection(db_name) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Error getting count for {table_name}: {str(e)}")
        return 0

def print_database_stats():
    reddit_count = get_table_count("reddit_data", "reddit_data")
    tiktok_count = get_table_count("tiktok_data", "tiktok_data")
    youtube_count = get_table_count("youtube_data", "youtube_data")
    
    logger.info("Current Database Stats:")
    logger.info(f"- Reddit posts: {reddit_count}")
    logger.info(f"- TikTok videos: {tiktok_count}")
    logger.info(f"- YouTube videos: {youtube_count}")
    
    return reddit_count, tiktok_count, youtube_count

def run_scrapers():
    try:
        logger.info("Starting scraping cycle...")
        
        # Get initial counts
        initial_reddit, initial_tiktok, initial_youtube = print_database_stats()
        
        # Run scrapers
        logger.info("Running Reddit scraper...")
        scrape_reddit()
        
        logger.info("Running TikTok scraper...")
        scrape_tiktok()
        
        logger.info("Running YouTube scraper...")
        scrape_youtube_trending()
        
        # Get final counts
        final_reddit, final_tiktok, final_youtube = print_database_stats()
        
        # Calculate and log differences
        logger.info("\nScraping Results:")
        logger.info(f"Reddit: +{final_reddit - initial_reddit} posts (Total: {final_reddit})")
        logger.info(f"TikTok: +{final_tiktok - initial_tiktok} videos (Total: {final_tiktok})")
        logger.info(f"YouTube: +{final_youtube - initial_youtube} videos (Total: {final_youtube})")
        
    except Exception as e:
        logger.error(f"Error in scraping cycle: {str(e)}")
        logger.exception("Detailed error:")

def main():
    logger.info("Starting main scraper...")
    
    while True:
        run_scrapers()
        logger.info("Waiting 15 minutes until next scrape cycle...")
        time.sleep(15 * 60)  # Wait 15 minutes

if __name__ == "__main__":
    main() 