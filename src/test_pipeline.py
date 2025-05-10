import logging
from pathlib import Path
from src.pipelines import social_media_analysis_pipeline
import pandas as pd
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pipeline():
    """Test the social media analysis pipeline."""
    try:
        # Create necessary directories
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        
        # Create a small test dataset
        test_data = pd.DataFrame({
            'platform': ['tiktok', 'youtube', 'reddit'] * 2,
            'text': [
                'This is a test post #trending',
                'Check out this video!',
                'Interesting discussion about AI',
                'Another test post #viral',
                'New tutorial video',
                'Tech news discussion'
            ],
            'timestamp': [1746038530, 1746038531, 1746038532, 1746038533, 1746038534, 1746038535],
            'engagement_score': [1000, 2000, 500, 1500, 3000, 800]
        })
        
        # Save test data
        test_data.to_csv("data/raw/test_data.csv", index=False)
        logger.info("Created test dataset")
        
        # Run pipeline
        logger.info("Starting pipeline test...")
        pipeline = social_media_analysis_pipeline()
        results = pipeline.run()
        
        # Verify outputs
        output_dir = Path("data/processed")
        required_files = [
            "engagement_model.joblib",
            "predictions.csv",
            "prediction_results.json",
            "exploration_results.json",
            "plots/actual_vs_predicted.png",
            "plots/residuals.png",
            "plots/residuals_distribution.png"
        ]
        
        missing_files = [f for f in required_files if not (output_dir / f).exists()]
        
        if missing_files:
            logger.error(f"Missing output files: {missing_files}")
            return False
        
        # Check prediction results
        with open(output_dir / "prediction_results.json", "r") as f:
            prediction_results = json.load(f)
            
        required_metrics = [
            'model_evaluation',
            'feature_importance',
            'predictions_summary'
        ]
        
        missing_metrics = [m for m in required_metrics if m not in prediction_results]
        
        if missing_metrics:
            logger.error(f"Missing metrics in results: {missing_metrics}")
            return False
        
        logger.info("Pipeline test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_pipeline() 