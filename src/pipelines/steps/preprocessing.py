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

def remove_emojis(text):
    if not isinstance(text, str):
        return ""
    emoji_pattern = re.compile(
        "[" 
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002700-\U000027BF"
        u"\U000024C2-\U0001F251"
        "]", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def get_wordnet_pos(tag):
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

def lemmatize_tokens(tokens):
    tagged = pos_tag(tokens)
    lemmatizer = WordNetLemmatizer()
    return [lemmatizer.lemmatize(w, get_wordnet_pos(t)) for w, t in tagged]

def preprocess_text(text, remove_stopwords=True):
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove emojis
    text = remove_emojis(text)
    
    # Remove special characters and numbers
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords if requested
    if remove_stopwords:
        stop_words = set(stopwords.words('english'))
        tokens = [t for t in tokens if t not in stop_words]
    
    # Lemmatize
    tokens = lemmatize_tokens(tokens)
    
    return ' '.join(tokens)

def extract_text_features(text):
    if not isinstance(text, str) or not text.strip():
        return {
            'word_count': 0,
            'char_count': 0,
            'avg_word_length': 0,
            'sentiment_score': 0,
            'sentiment_subjectivity': 0
        }
    words = text.split()
    blob = TextBlob(text)
    return {
        'word_count': len(words),
        'char_count': len(text),
        'avg_word_length': len(text) / len(words) if len(words) > 0 else 0,
        'sentiment_score': blob.sentiment.polarity,
        'sentiment_subjectivity': blob.sentiment.subjectivity
    }

@step
def preprocess_data(data: pd.DataFrame) -> pd.DataFrame:
    """Preprocess the social media data as in the notebook."""
    logger.info(f"Starting preprocessing with input data shape: {data.shape}")
    
    # Make a copy to avoid modifying the original
    df = data.copy()
    
    # 1. Check for required columns
    required_columns = ['platform', 'content', 'engagement', 'timestamp']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        raise ValueError(f"Required columns missing: {missing_columns}")
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        logger.info("Converting timestamp column to datetime...")
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        null_timestamps = df['timestamp'].isnull().sum()
        if null_timestamps > 0:
            logger.warning(f"Found {null_timestamps} invalid timestamps. These rows will be dropped.")
            df = df.dropna(subset=['timestamp'])
            if len(df) == 0:
                raise ValueError("No valid timestamps found after conversion.")
    
    # 2. Basic cleaning
    logger.info("Performing basic cleaning...")
    df['text'] = df['content'].fillna('')
    logger.info(f"Data shape after basic cleaning: {df.shape}")
    
    # 3. Engagement calculation
    logger.info("Calculating engagement scores...")
    if 'engagement' not in df.columns:
        # Platform-specific engagement calculation
        for platform in df['platform'].unique():
            platform_mask = df['platform'] == platform
            if platform == 'tiktok':
                if {'likes','shares','comments'}.issubset(df.columns):
                    df.loc[platform_mask, 'engagement'] = df.loc[platform_mask, ['likes','shares','comments']].fillna(0).astype(float).sum(axis=1)
            elif platform == 'reddit':
                if {'score','num_comments'}.issubset(df.columns):
                    df.loc[platform_mask, 'engagement'] = df.loc[platform_mask, ['score','num_comments']].fillna(0).astype(float).sum(axis=1)
                elif {'score','comments'}.issubset(df.columns):
                    df.loc[platform_mask, 'engagement'] = df.loc[platform_mask, ['score','comments']].fillna(0).astype(float).sum(axis=1)
            elif platform == 'youtube':
                if {'like_count','comment_count','view_count'}.issubset(df.columns):
                    df.loc[platform_mask, 'engagement'] = df.loc[platform_mask, ['like_count','comment_count','view_count']].fillna(0).astype(float).sum(axis=1)
                elif {'likes','comments','views'}.issubset(df.columns):
                    df.loc[platform_mask, 'engagement'] = df.loc[platform_mask, ['likes','comments','views']].fillna(0).astype(float).sum(axis=1)
        
        # If engagement is still not calculated for some rows, set to 0
        df['engagement'] = df['engagement'].fillna(0)
    
    logger.info(f"Engagement score range: {df['engagement'].min()} to {df['engagement'].max()}")
    
    # 4. Text preprocessing
    logger.info("Preprocessing text...")
    # Combine title and text if both exist
    if 'title' in df.columns and 'text' in df.columns:
        df['combined_text'] = df['title'].fillna('') + ' ' + df['text'].fillna('')
    else:
        df['combined_text'] = df['text'].fillna('')
    
    df['lemmatized_text'] = df['combined_text'].astype(str).apply(lambda x: preprocess_text(x, remove_stopwords=True))
    logger.info(f"Data shape after text preprocessing: {df.shape}")
    
    # Log text preprocessing results
    empty_texts = df['lemmatized_text'].str.strip().eq('').sum()
    logger.info(f"Number of empty texts after preprocessing: {empty_texts}")
    
    # 5. Feature extraction
    logger.info("Extracting text features...")
    features = df['lemmatized_text'].apply(extract_text_features)
    features_df = pd.DataFrame(features.tolist())
    df = pd.concat([df, features_df], axis=1)
    logger.info(f"Data shape after feature extraction: {df.shape}")
    
    # 6. Time-based features
    logger.info("Adding time-based features...")
    try:
        # Ensure timestamp is in UTC
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['date'] = df['timestamp'].dt.date
        logger.info(f"Data shape after adding time features: {df.shape}")
    except Exception as e:
        logger.error(f"Error adding time-based features: {str(e)}")
        logger.error(f"Timestamp column type: {df['timestamp'].dtype}")
        logger.error(f"Sample timestamps: {df['timestamp'].head()}")
        raise
    
    # 7. Engagement normalization
    logger.info("Normalizing engagement scores...")
    min_eng = df['engagement'].min()
    max_eng = df['engagement'].max()
    if max_eng > min_eng:
        df['engagement_score'] = (df['engagement'] - min_eng) / (max_eng - min_eng)
    else:
        df['engagement_score'] = 0
    logger.info(f"Normalized engagement score range: {df['engagement_score'].min()} to {df['engagement_score'].max()}")
    
    # 8. Final validation
    if len(df) == 0:
        logger.error("No data left after preprocessing! Please check raw data and preprocessing steps.")
        raise ValueError("No data left after preprocessing. Check raw data and preprocessing steps.")

    # Add normalized_engagement as alias for engagement_score
    df['normalized_engagement'] = df['engagement_score']

    logger.info(f"Preprocessing complete. Final dataset shape: {df.shape}")
    return df 