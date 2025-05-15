from zenml.pipelines import pipeline
from zenml.config import DockerSettings
from zenml.integrations.constants import SKLEARN
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path("data/logs/pipeline.log").resolve())
    ]
)

logger = logging.getLogger("zenml_pipeline")

# Import steps
from src.pipelines.steps.data_ingestion import ingest_data
from src.pipelines.steps.preprocessing import preprocess_data
from src.pipelines.steps.data_exploration import explore_data
from src.pipelines.steps.predictions import make_predictions

# Docker Settings
docker_settings = DockerSettings(required_integrations=[SKLEARN])

@pipeline(enable_cache=True, settings={"docker": docker_settings})
def trend_analysis_pipeline():
    """
    ZenML Pipeline for the Social Media Trend Analysis Project.
    
    This pipeline combines data from multiple social media sources,
    analyzes trends, and predicts user engagement.
    
    Steps:
    1. Data Ingestion: Load and unify data from different social media platforms
    2. Preprocessing: Clean and normalize the data
    3. Data Exploration: Perform EDA and analyze patterns
    4. Make Predictions: Build and train a model for engagement prediction
    """
    logger.info("Starting trend analysis pipeline")
    
    try:
        # Step 1: Load and unify data
        logger.info("Step 1: Data Ingestion - Loading and unifying data")
        raw_data = ingest_data()
        logger.info(f"Data ingestion complete, received dataframe with shape: {raw_data.shape if hasattr(raw_data, 'shape') else 'unknown'}")

        # Step 2: Clean and enrich data
        logger.info("Step 2: Preprocessing - Cleaning and enriching data")
        processed_data = preprocess_data(raw_data)
        logger.info(f"Data preprocessing complete, resulting dataframe shape: {processed_data.shape if hasattr(processed_data, 'shape') else 'unknown'}")

        # Step 3: Exploratory data analysis
        logger.info("Step 3: Data Exploration - Analyzing patterns and trends")
        exploration_results = explore_data(processed_data)
        logger.info("Data exploration complete")

        # Step 4: Make predictions
        logger.info("Step 4: Predictions - Building and training engagement prediction model")
        prediction_results = make_predictions(processed_data, exploration_results)
        logger.info("Prediction process complete")
        
        logger.info("Pipeline execution completed successfully")
        return prediction_results
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        logger.error(f"Error details: {e}")
        raise

if __name__ == "__main__":
    # Create necessary directories
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    # Log pipeline start
    logger.info("===== Starting TrendAnalyseSocialMedia Pipeline =====")
    
    try:
        # Run the pipeline
        result = trend_analysis_pipeline()
        logger.info("Pipeline executed successfully!")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        logger.exception("Exception details:")
    finally:
        logger.info("===== Pipeline Execution Complete =====")
