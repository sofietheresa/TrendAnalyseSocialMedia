import os
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import psycopg2
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from jobs.reddit_scraper import scrape_reddit
from jobs.tiktok_scraper import trending_videos as scrape_tiktok
from jobs.youtube_scraper import scrape_youtube_trending
import pandas as pd

# Load environment variables
load_dotenv()

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

def get_db_connection():
    """
    Connect to the main railway database specified in DATABASE_URL
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

def get_table_count(table_name):
    """Get the number of records in a table from the railway database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Query the public schema (most common)
                cur.execute(f"SELECT COUNT(*) FROM public.{table_name}")
                return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Error getting count for {table_name}: {str(e)}")
        return 0

def print_database_stats():
    """Get and log current database statistics"""
    try:
        # Get counts for each platform's table in the railway database
        reddit_count = get_table_count("reddit_data")
        tiktok_count = get_table_count("tiktok_data") 
        youtube_count = get_table_count("youtube_data")
        
        logger.info("Current Database Stats:")
        logger.info(f"- Reddit posts: {reddit_count}")
        logger.info(f"- TikTok videos: {tiktok_count}")
        logger.info(f"- YouTube videos: {youtube_count}")
        
        return reddit_count, tiktok_count, youtube_count
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return 0, 0, 0

def run_scrapers():
    """Run all scrapers and log the results"""
    try:
        logger.info("Starting scraping cycle...")
        start_time = datetime.now()
        
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
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Scraping cycle completed in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error in scraping cycle: {str(e)}")
        logger.exception("Detailed error:")

def main():
    """Main scheduler function"""
    logger.info("Starting main scraper scheduler...")
    
    try:
        # Run scrapers immediately on start
        run_scrapers()
        
        # Then run in a loop with 15 minute intervals
        while True:
            next_run = datetime.now() + pd.Timedelta(minutes=15)
            logger.info(f"Next scrape cycle scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(15 * 60)  # Wait 15 minutes
            run_scrapers()
            
    except KeyboardInterrupt:
        logger.info("Scraper scheduler stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}")
        logger.exception("Detailed error:")

if __name__ == "__main__":
    main() 