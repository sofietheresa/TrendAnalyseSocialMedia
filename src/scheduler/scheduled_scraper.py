import os
import time
import schedule
from datetime import datetime
import signal
from functools import wraps
from dotenv import load_dotenv
from run_all_scrapers import run_all
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
HEALTH_FILE = BASE_DIR / "scheduler_health.txt"

# Logging setup with rotation
log_handler = RotatingFileHandler(
    LOG_DIR / "scheduled_scraper.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=5
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger = logging.getLogger("scheduled_scraper")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Also add a console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger.addHandler(console_handler)

def update_health_file():
    """Update the health check file with current timestamp"""
    try:
        with open(HEALTH_FILE, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Failed to update health file: {e}")

def with_retry(max_retries=3, delay=5):
    """Decorator to retry failed operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Failed after {max_retries} retries: {e}")
                        raise
                    logger.warning(f"Attempt {retries} failed: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@with_retry(max_retries=3, delay=5)
def scheduled_scraping():
    try:
        logger.info(f"Starting scheduled scraping at {datetime.now()}")
        run_all()
        logger.info(f"Completed scheduled scraping at {datetime.now()}")
        update_health_file()
    except Exception as e:
        logger.error(f"Error in scheduled scraping: {str(e)}")
        logger.exception("Detailed error:")
        raise

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    # You could add cleanup code here if needed
    exit(0)

def run_scheduler():
    logger.info("Starting scheduled scraper")
    print("Scheduled scraper started. Press Ctrl+C to stop.")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Schedule jobs to run every 15 minutes
    schedule.every(15).minutes.do(scheduled_scraping)
    
    # Run immediately on startup
    scheduled_scraping()
    
    try:
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.error(f"Unexpected error in scheduler: {e}")
        logger.exception("Detailed error:")
        raise
    finally:
        logger.info("Scraper stopped")
        print("\nScraper stopped. Goodbye!")

if __name__ == "__main__":
    run_scheduler() 