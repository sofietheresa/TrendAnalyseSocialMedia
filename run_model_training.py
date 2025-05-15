#!/usr/bin/env python
"""
Run Model Training Script

This script runs the ML model training pipeline on real data and outputs
metrics to be displayed in the frontend.
"""

import os
import sys
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_model_training")

def main():
    """Main function to run the model training"""
    parser = argparse.ArgumentParser(description='Run model training pipeline')
    parser.add_argument('--model', type=str, default='topic_model',
                        choices=['topic_model', 'sentiment_classifier', 'anomaly_detector'],
                        help='Model type to train')
    parser.add_argument('--data-path', type=str, default='data/processed',
                        help='Path to processed data')
    args = parser.parse_args()
    
    try:
        # Import at runtime to avoid circular imports
        from src.pipelines.mlops_pipeline import run_mlops_pipeline
        
        # Ensure output directories exist
        models_dir = Path('models/registry')
        models_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting model training for {args.model}")
        
        # Run the pipeline
        results = run_mlops_pipeline(
            model_name=args.model,
            data_path=args.data_path
        )
        
        # Print results
        logger.info("Model training completed with results:")
        print(json.dumps(results, indent=2))
        
        # Return success
        return 0
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure all required dependencies are installed")
        return 1
        
    except Exception as e:
        logger.error(f"Error running model training: {e}")
        logger.exception("Exception details:")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 