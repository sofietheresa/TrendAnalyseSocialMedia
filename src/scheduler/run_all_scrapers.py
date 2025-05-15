import os
import importlib.util
from datetime import datetime
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import asyncio

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
JOBS_DIR = BASE_DIR / "jobs"
LOG_DIR = BASE_DIR.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging setup with rotation
log_handler = RotatingFileHandler(
    LOG_DIR / "run_all_scrapers.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=5
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger = logging.getLogger("run_all_scrapers")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

def import_module_from_file(file_path):
    """Import a module from file path"""
    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_script(script_path):
    """Run a scraper script by importing it and calling its main function"""
    name = script_path.stem
    start = datetime.now()

    try:
        # Import the script module directly from file
        module = import_module_from_file(script_path)
        
        # Get the main function (scrape_reddit, trending_videos, scrape_youtube_trending)
        main_func = None
        if hasattr(module, "scrape_reddit"):
            main_func = module.scrape_reddit
        elif hasattr(module, "trending_videos"):
            main_func = module.trending_videos
        elif hasattr(module, "scrape_youtube_trending"):
            main_func = module.scrape_youtube_trending
        
        if main_func:
            logger.info(f"Starting {name}...")
            if asyncio.iscoroutinefunction(main_func):
                asyncio.run(main_func())
            else:
                main_func()
            duration = (datetime.now() - start).seconds
            logger.info(f"Successfully completed {name} in {duration} seconds")
        else:
            logger.error(f"Could not find main function in {name}")

    except Exception as e:
        logger.error(f"Error running {name}: {str(e)}")
        logger.exception("Detailed error:")

def run_all():
    """Run all scraper scripts in the jobs directory"""
    # Find all scraper scripts
    scraper_scripts = sorted(JOBS_DIR.glob("*_scraper.py"))
    
    for script in scraper_scripts:
        logger.info(f"Running script: {script.name}")
        run_script(script)

if __name__ == "__main__":
    run_all()
