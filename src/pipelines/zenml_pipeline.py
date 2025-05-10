from zenml import pipeline, step
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

@step
def load_data(file_path: str) -> pd.DataFrame:
    """
    Load data from a file.
    """
    try:
        data = pd.read_csv(file_path)
        return data
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

@step
def preprocess_data(data: pd.DataFrame) -> Tuple[pd.DataFrame, Tuple[int, int]]:
    """
    Preprocess the input data.
    """
    # Basic preprocessing steps
    data = data.dropna()  # Remove missing values
    data = data.drop_duplicates()  # Remove duplicates
    
    # Convert date columns if they exist
    date_columns = [col for col in data.columns if 'date' in col.lower()]
    for col in date_columns:
        data[col] = pd.to_datetime(data[col])
    
    return data, data.shape

@step
def analyze_sentiment(data: pd.DataFrame, text_column: str) -> Dict:
    """
    Perform sentiment analysis on the preprocessed data.
    """
    # TODO: Implement sentiment analysis using your preferred library
    # For now, return dummy sentiment scores
    sentiment_scores = np.random.normal(0, 1, len(data))
    
    return {
        "sentiment_scores": sentiment_scores.tolist(),
        "timestamp": datetime.now().isoformat()
    }

@step
def model_topics(data: pd.DataFrame, text_column: str, n_topics: int = 5) -> Dict:
    """
    Perform topic modeling on the preprocessed data.
    """
    # TODO: Implement topic modeling using your preferred library
    # For now, return dummy topics
    topics = [f"Topic {i}" for i in range(n_topics)]
    
    return {
        "topics": topics,
        "timestamp": datetime.now().isoformat()
    }

@pipeline
def social_media_analysis_pipeline(
    input_file: str,
    text_column: str = "text",
    n_topics: int = 5
) -> Dict:
    """
    Main pipeline for social media analysis.
    """
    # Load the data
    data = load_data(input_file)
    
    # Preprocess the data
    preprocessed_data, data_shape = preprocess_data(data)
    
    # Analyze sentiment
    sentiment_results = analyze_sentiment(preprocessed_data, text_column)
    
    # Model topics
    topic_results = model_topics(preprocessed_data, text_column, n_topics)
    
    return {
        "sentiment": sentiment_results,
        "topics": topic_results,
        "preprocessed_data_shape": data_shape
    } 