from zenml.pipelines import pipeline
from zenml.config import DockerSettings
from zenml.integrations.constants import SKLEARN

# Import steps
from src.pipelines.steps.data_ingestion import ingest_data
from src.pipelines.steps.preprocessing import preprocess_data
from src.pipelines.steps.data_exploration import explore_data
from src.pipelines.steps.predictions import make_predictions

# Docker Settings
docker_settings = DockerSettings(required_integrations=[SKLEARN])

@pipeline(enable_cache=True, settings={"docker": docker_settings})
def trend_analysis_pipeline():
    # Step 1: Load and unify data
    raw_data = ingest_data()

    # Step 2: Clean and enrich data
    processed_data = preprocess_data(raw_data)

    # Step 3: Exploratory data analysis
    exploration_results = explore_data(processed_data)

    # Step 4: Make predictions
    prediction_results = make_predictions(processed_data, exploration_results)

if __name__ == "__main__":
    # Run the pipeline
    trend_analysis_pipeline()
