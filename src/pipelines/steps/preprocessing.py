from src.pipelines import step
import pandas as pd
import numpy as np
import logging
import re
import string
from typing import Dict, Any, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer, PorterStemmer

# Configure logger
logger = logging.getLogger(__name__)

# Download NLTK resources if needed
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

@step
def preprocess_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocesses the social media data by cleaning text and extracting features.
    
    Args:
        data: Raw social media data
        
    Returns:
        Preprocessed data with cleaned text and extracted features
    """
    if data.empty:
        logger.warning("Input data is empty. Returning empty DataFrame.")
        return pd.DataFrame()
    
    logger.info(f"Preprocessing data with shape {data.shape}")
    
    # Make a copy to avoid modifying the original
    df = data.copy()
    
    # 1. Basic text preprocessing
    if 'content' in df.columns:
        logger.info("Performing text preprocessing...")
        
        # Clean text
        df['cleaned_text'] = df['content'].fillna('').astype(str).apply(clean_text)
        
        # Extract text features
        logger.info("Extracting text features...")
        df['text_length'] = df['content'].fillna('').astype(str).apply(len)
        df['word_count'] = df['cleaned_text'].apply(lambda x: len(x.split()) if x else 0)
        df['has_url'] = df['content'].fillna('').astype(str).apply(lambda x: 1 if 'http' in x.lower() else 0)
        df['has_mention'] = df['content'].fillna('').astype(str).apply(lambda x: 1 if '@' in x else 0)
        df['has_hashtag'] = df['content'].fillna('').astype(str).apply(lambda x: 1 if '#' in x else 0)
        
        # Extract hashtags
        df['hashtags'] = df['content'].fillna('').astype(str).apply(extract_hashtags)
    
    # 2. Platform-specific features
    if 'platform' in df.columns:
        logger.info("Adding platform-specific features...")
        
        # Create one-hot encoded platform columns
        platform_dummies = pd.get_dummies(df['platform'], prefix='platform')
        df = pd.concat([df, platform_dummies], axis=1)
    
    # 3. Handling missing values
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('')
        elif pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
    
    # 4. Date features if timestamp column exists
    if 'timestamp' in df.columns:
        logger.info("Extracting time-based features...")
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Filter out rows with invalid timestamps
        df = df.dropna(subset=['timestamp'])
        
        if not df.empty:
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['hour_of_day'] = df['timestamp'].dt.hour
            df['is_weekend'] = df['timestamp'].dt.dayofweek.isin([5, 6]).astype(int)
    
    # 5. Normalize engagement score
    if 'engagement' in df.columns:
        logger.info("Normalizing engagement scores...")
        # If engagement score exists, normalize it per platform
        if 'platform' in df.columns:
            for platform in df['platform'].unique():
                platform_mask = df['platform'] == platform
                if platform_mask.sum() > 0:
                    platform_mean = df.loc[platform_mask, 'engagement'].mean()
                    platform_std = df.loc[platform_mask, 'engagement'].std()
                    
                    if platform_std > 0:  # Avoid division by zero
                        df.loc[platform_mask, 'normalized_engagement'] = (
                            (df.loc[platform_mask, 'engagement'] - platform_mean) / platform_std
                        )
                    else:
                        df.loc[platform_mask, 'normalized_engagement'] = 0
        else:
            # Global normalization if no platform column
            mean_engagement = df['engagement'].mean()
            std_engagement = df['engagement'].std()
            
            if std_engagement > 0:  # Avoid division by zero
                df['normalized_engagement'] = (df['engagement'] - mean_engagement) / std_engagement
            else:
                df['normalized_engagement'] = 0
    
    logger.info(f"Preprocessing complete. Final shape: {df.shape}")
    return df

# Helper functions for text preprocessing
def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove special characters and numbers
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_hashtags(text: str) -> str:
    """Extract hashtags from text and return as comma-separated string"""
    hashtags = re.findall(r'#(\w+)', text)
    return ','.join(hashtags)

# Advanced NLP functions - can be used to extend the preprocessing
def lemmatize_text(text: str) -> str:
    """Lemmatize text to reduce words to their root form"""
    lemmatizer = WordNetLemmatizer()
    word_tokens = word_tokenize(text)
    return ' '.join([lemmatizer.lemmatize(word) for word in word_tokens])

def remove_stopwords(text: str) -> str:
    """Remove stopwords from text"""
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    return ' '.join([word for word in word_tokens if word.lower() not in stop_words]) 