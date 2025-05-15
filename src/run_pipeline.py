#!/usr/bin/env python3
"""
Script to run the ZenML Trend Analysis Pipeline
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("pipeline_runner")

def setup_environment():
    """Setup environment and create necessary directories"""
    # Create necessary directories
    data_dir = Path("data")
    logs_dir = data_dir / "logs"
    processed_dir = data_dir / "processed"
    
    for dir_path in [data_dir, logs_dir, processed_dir]:
        dir_path.mkdir(exist_ok=True, parents=True)
        logger.info(f"Created directory: {dir_path}")
    
    # Setup log file handler
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"pipeline_run_{timestamp}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add file handler to root logger
    logging.getLogger().addHandler(file_handler)
    logger.info(f"Logging to file: {log_file}")
    
    # Set environment variables if needed
    os.environ["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return log_file

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run the Social Media Trend Analysis Pipeline")
    parser.add_argument("--skip-cache", action="store_true", help="Skip cached results and rerun all steps")
    parser.add_argument("--debug", action="store_true", help="Enable debug logs")
    
    return parser.parse_args()

def main():
    """Main function to run the pipeline"""
    args = parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")
    
    # Setup environment
    log_file = setup_environment()
    
    try:
        # Import the pipeline (import here to capture any import errors properly)
        logger.info("Importing the pipeline...")
        from src.pipelines.zenml_pipeline import trend_analysis_pipeline
        
        # Run the pipeline
        logger.info("===== Starting TrendAnalyseSocialMedia Pipeline =====")
        
        # Run with or without cache
        if args.skip_cache:
            logger.info("Running pipeline with cache disabled")
            result = trend_analysis_pipeline(enable_cache=False)
        else:
            logger.info("Running pipeline with cache enabled")
            result = trend_analysis_pipeline()
        
        logger.info("Pipeline executed successfully!")
        logger.info(f"Check the logs for details: {log_file}")
        
        return 0
    except ImportError as e:
        logger.error(f"Failed to import the pipeline: {e}")
        logger.error("Make sure you have all required dependencies installed")
        return 1
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        logger.exception("Exception details:")
        return 1
    finally:
        logger.info("===== Pipeline Execution Complete =====")

if __name__ == "__main__":
    sys.exit(main()) 