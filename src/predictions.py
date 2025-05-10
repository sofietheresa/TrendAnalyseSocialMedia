import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from prophet import Prophet
import matplotlib.pyplot as plt
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/predictions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TopicPredictor:
    def __init__(self, data_path: str):
        """Initialize the TopicPredictor with data path."""
        self.data_path = data_path
        self.df = None
        self.vectorizer = None
        self.model = None
        self.logger = logging.getLogger(__name__)

    def load_data(self):
        """Load and preprocess the data."""
        try:
            self.df = pd.read_csv(self.data_path)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], errors='coerce')
            self.df = self.df.dropna(subset=['timestamp'])
            self.df['date'] = self.df['timestamp'].dt.date
            self.logger.info("Data loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def train_topic_classifier(self):
        """Train a classifier to predict topics from text."""
        try:
            # Prepare features and target
            X_text = self.df['text_clean'].astype(str)
            y_topic = self.df['topic']

            # TF-IDF vectorization
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            X = self.vectorizer.fit_transform(X_text)

            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_topic, test_size=0.2, stratify=y_topic, random_state=42
            )

            # Train model
            self.model = LogisticRegression(max_iter=200)
            self.model.fit(X_train, y_train)

            # Evaluate
            y_pred = self.model.predict(X_test)
            report = classification_report(y_test, y_pred)
            self.logger.info(f"Model evaluation:\n{report}")

            return report

        except Exception as e:
            self.logger.error(f"Error training topic classifier: {str(e)}")
            raise

    def predict_topic(self, text: str) -> int:
        """Predict topic for new text."""
        if not self.model or not self.vectorizer:
            raise ValueError("Model not trained. Call train_topic_classifier first.")
        
        try:
            X = self.vectorizer.transform([text])
            return self.model.predict(X)[0]
        except Exception as e:
            self.logger.error(f"Error predicting topic: {str(e)}")
            raise

class TopicTrendAnalyzer:
    def __init__(self, data_path: str):
        """Initialize the TopicTrendAnalyzer with data path."""
        self.data_path = data_path
        self.df = None
        self.logger = logging.getLogger(__name__)

    def load_data(self):
        """Load and preprocess the data."""
        try:
            self.df = pd.read_csv(self.data_path)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], errors='coerce')
            self.df = self.df.dropna(subset=['timestamp'])
            self.df['date'] = self.df['timestamp'].dt.date
            self.logger.info("Data loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            raise

    def analyze_topic_trends(self, topic_id: int, forecast_days: int = 14):
        """Analyze trends for a specific topic using Prophet."""
        try:
            # Prepare data for the topic
            df_topic = self.df[self.df['topic'] == topic_id].groupby('date').size().reset_index(name='count')
            df_topic.columns = ['ds', 'y']

            # Fit Prophet model
            model = Prophet()
            model.fit(df_topic)

            # Make future predictions
            future = model.make_future_dataframe(periods=forecast_days)
            forecast = model.predict(future)

            # Plot results
            fig = model.plot(forecast)
            plt.title(f'Topic {topic_id} Forecast')
            plt.savefig(f'results/topic_{topic_id}_forecast.png')
            plt.close()

            self.logger.info(f"Topic {topic_id} trend analysis completed")
            return forecast

        except Exception as e:
            self.logger.error(f"Error analyzing topic trends: {str(e)}")
            raise

    def analyze_sentiment_trends(self, topic_id: int):
        """Analyze sentiment trends for a specific topic."""
        try:
            # Filter data for the topic
            df_topic = self.df[self.df['topic'] == topic_id].copy()
            
            # Calculate daily sentiment statistics
            sentiment_stats = df_topic.groupby('date').agg({
                'sentiment': ['mean', 'std', 'count']
            }).reset_index()
            
            # Plot sentiment trends
            plt.figure(figsize=(12, 6))
            plt.plot(sentiment_stats['date'], sentiment_stats[('sentiment', 'mean')], 
                    label='Mean Sentiment')
            plt.fill_between(sentiment_stats['date'],
                           sentiment_stats[('sentiment', 'mean')] - sentiment_stats[('sentiment', 'std')],
                           sentiment_stats[('sentiment', 'mean')] + sentiment_stats[('sentiment', 'std')],
                           alpha=0.2)
            plt.title(f'Sentiment Trends for Topic {topic_id}')
            plt.xlabel('Date')
            plt.ylabel('Sentiment Score')
            plt.legend()
            plt.savefig(f'results/topic_{topic_id}_sentiment.png')
            plt.close()

            self.logger.info(f"Sentiment analysis for topic {topic_id} completed")
            return sentiment_stats

        except Exception as e:
            self.logger.error(f"Error analyzing sentiment trends: {str(e)}")
            raise

def main():
    """Main function to run the analysis pipeline."""
    try:
        # Create necessary directories
        Path('logs').mkdir(exist_ok=True)
        Path('results').mkdir(exist_ok=True)

        # Initialize and run topic prediction
        predictor = TopicPredictor('data/processed/social_media_data_with_topics.csv')
        predictor.load_data()
        predictor.train_topic_classifier()

        # Initialize and run trend analysis
        analyzer = TopicTrendAnalyzer('data/processed/social_media_data_with_topics.csv')
        analyzer.load_data()

        # Analyze trends for each topic
        for topic_id in analyzer.df['topic'].unique():
            analyzer.analyze_topic_trends(topic_id)
            analyzer.analyze_sentiment_trends(topic_id)

    except Exception as e:
        logger.error(f"Error in main pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main() 