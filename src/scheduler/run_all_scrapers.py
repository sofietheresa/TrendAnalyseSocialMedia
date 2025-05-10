import os
from pathlib import Path
import logging
from datetime import datetime
from src.scrapers.tiktok_scraper import TikTokScraper
from src.scrapers.youtube_scraper import YouTubeScraper
from src.scrapers.reddit_scraper import RedditScraper

# Create logs directory in the project root
logs_dir = Path("logs")
logs_dir.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / f"scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_all():
    """Run all scrapers and combine their results."""
    try:
        # Initialize scrapers
        tiktok_scraper = TikTokScraper()
        youtube_scraper = YouTubeScraper()
        reddit_scraper = RedditScraper()

        # Run scrapers
        logger.info("Starting TikTok scraping...")
        tiktok_data = tiktok_scraper.scrape()
        logger.info(f"TikTok scraping completed. Found {len(tiktok_data)} posts.")

        logger.info("Starting YouTube scraping...")
        youtube_data = youtube_scraper.scrape()
        logger.info(f"YouTube scraping completed. Found {len(youtube_data)} posts.")

        logger.info("Starting Reddit scraping...")
        reddit_data = reddit_scraper.scrape()
        logger.info(f"Reddit scraping completed. Found {len(reddit_data)} posts.")

        # Combine all data
        all_data = tiktok_data + youtube_data + reddit_data
        logger.info(f"Total posts collected: {len(all_data)}")

        return all_data

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise

if __name__ == "__main__":
    run_all()
