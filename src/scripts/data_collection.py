import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
import sys

# Add scheduler directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scheduler")))
from scheduler.run_all_scrapers import run_all
from scheduler.jobs.reddit_scraper import scrape_reddit
from scheduler.jobs.tiktok_scraper import scrape_tiktok
from scheduler.jobs.youtube_scraper import scrape_youtube

# Setup logging
log_path = Path("logs/data_collection.log")
log_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def collect_data():
    """Collect data from all platforms using the scheduler jobs"""
    try:
        logging.info("Starting data collection from all platforms")
        
        # Create data directory if it doesn't exist
        Path('data/raw').mkdir(parents=True, exist_ok=True)
        
        # Run all scrapers using the scheduler
        run_all()
        
        logging.info("Data collection completed successfully")
        
    except Exception as e:
        logging.error(f"Error in data collection: {str(e)}")
        raise

def main():
    """Main function to collect data from all platforms"""
    try:
        collect_data()
    except Exception as e:
        logging.error(f"Error in main data collection: {str(e)}")
        raise

if __name__ == "__main__":
    main() 