from src.pipelines.zenml_pipeline import (
    load_data,
    preprocess_data,
    analyze_sentiment,
    model_topics
)
import pandas as pd
import os

def main():
    # Create a sample dataset
    data = pd.DataFrame({
        'text': ['This is a positive review', 'This is a negative review', 'This is a neutral review'],
        'date': ['2024-01-01', '2024-01-02', '2024-01-03']
    })
    
    # Save the sample data
    os.makedirs('data/raw', exist_ok=True)
    data.to_csv('data/raw/sample_data.csv', index=False)
    
    # Run the pipeline steps directly
    data = load_data('data/raw/sample_data.csv')
    preprocessed_data, data_shape = preprocess_data(data)
    sentiment_results = analyze_sentiment(preprocessed_data, 'text')
    topic_results = model_topics(preprocessed_data, 'text', 3)
    
    print("Pipeline Results (direkt):")
    print(f"Preprocessed data shape: {data_shape}")
    print(f"Sentiment analysis timestamp: {sentiment_results['timestamp']}")
    print(f"Topic modeling timestamp: {topic_results['timestamp']}")

if __name__ == "__main__":
    main() 