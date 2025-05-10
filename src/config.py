from zenml.config import DockerSettings
from zenml.integrations.constants import SKLEARN, TENSORFLOW
from zenml.pipelines import pipeline

# Define the Docker settings
docker_settings = DockerSettings(
    requirements=[
        "zenml",
        "pandas",
        "numpy",
        "scikit-learn",
        "nltk",
        "textblob",
        "tensorflow",
    ]
)

# Define pipeline settings
@pipeline(
    enable_cache=True,
    settings={"docker": docker_settings}
)
def social_media_analysis_pipeline():
    """Main pipeline that orchestrates all steps."""
    pass 