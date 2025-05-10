from zenml.steps import step
import pandas as pd
import numpy as np
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
from textblob import TextBlob
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

def get_wordnet_pos(tag: str) -> str:
    """Convert POS tag to WordNet POS tag."""
    tag_dict = {
        "J": wordnet.ADJ,
        "N": wordnet.NOUN,
        "V": wordnet.VERB,
        "R": wordnet.ADV
    }
    return tag_dict.get(tag[0], wordnet.NOUN)

def clean_text(text: str) -> str:
    """Clean and preprocess text."""
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove special characters and numbers
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def lemmatize_text(text: str) -> str:
    """Lemmatize text using NLTK."""
    if not isinstance(text, str) or not text.strip():
        return ""
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Get POS tags
    pos_tags = pos_tag(tokens)
    
    # Initialize lemmatizer
    lemmatizer = WordNetLemmatizer()
    
    # Lemmatize each token
    lemmatized = [
        lemmatizer.lemmatize(token, get_wordnet_pos(tag))
        for token, tag in pos_tags
    ]
    
    return ' '.join(lemmatized)

def remove_stopwords(text: str) -> str:
    """Remove stopwords from text."""
    if not isinstance(text, str) or not text.strip():
        return ""
    
    # Get stopwords
    stop_words = set(stopwords.words('english'))
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    filtered_tokens = [word for word in tokens if word.lower() not in stop_words]
    
    return ' '.join(filtered_tokens)

def get_sentiment(text: str) -> float:
    """Get sentiment score using TextBlob."""
    if not isinstance(text, str) or not text.strip():
        return 0.0
    
    return TextBlob(text).sentiment.polarity

@step
def preprocess_data(data: pd.DataFrame) -> pd.DataFrame:
    """Preprocess the social media data."""
    logger.info("Starting data preprocessing...")
    
    # Make a copy to avoid modifying the original
    df = data.copy()
    
    # Clean text
    logger.info("Cleaning text...")
    df['cleaned_text'] = df['text'].apply(clean_text)
    
    # Remove stopwords
    logger.info("Removing stopwords...")
    df['text_no_stopwords'] = df['cleaned_text'].apply(remove_stopwords)
    
    # Lemmatize text
    logger.info("Lemmatizing text...")
    df['lemmatized_text'] = df['text_no_stopwords'].apply(lemmatize_text)
    
    # Add sentiment analysis
    logger.info("Adding sentiment analysis...")
    df['sentiment_score'] = df['cleaned_text'].apply(get_sentiment)
    
    # Convert timestamp to datetime
    logger.info("Converting timestamps...")
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    
    # Add time-based features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    
    # Normalize engagement score
    logger.info("Normalizing engagement scores...")
    df['normalized_engagement'] = (df['engagement_score'] - df['engagement_score'].min()) / \
                                (df['engagement_score'].max() - df['engagement_score'].min())
    
    # Drop rows with empty text
    df = df[df['cleaned_text'].str.len() > 0]
    
    logger.info(f"Preprocessing complete. Final dataset shape: {df.shape}")
    
    return df 