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
import emoji

logger = logging.getLogger(__name__)

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

def remove_emojis(text):
    if not isinstance(text, str):
        return ""
    return emoji.replace_emoji(text, replace='')

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
    """Preprocess the social media data from the SQLite database."""
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
    
    # 3. Platform-specific processing
    logger.info("Performing platform-specific processing...")
    
    # TikTok specific
    tiktok_mask = df['platform'] == 'tiktok'
    if tiktok_mask.any():
        df.loc[tiktok_mask, 'engagement'] = df.loc[tiktok_mask, ['likes', 'shares', 'comments']].fillna(0).sum(axis=1)
    
    # Reddit specific
    reddit_mask = df['platform'] == 'reddit'
    if reddit_mask.any():
        df.loc[reddit_mask, 'engagement'] = df.loc[reddit_mask, ['score', 'num_comments']].fillna(0).sum(axis=1)
    
    # YouTube specific
    youtube_mask = df['platform'] == 'youtube'
    if youtube_mask.any():
        df.loc[youtube_mask, 'engagement'] = df.loc[youtube_mask, ['like_count', 'comment_count', 'view_count']].fillna(0).sum(axis=1)
    
    # Rename engagement to engagement_score
    df.rename(columns={'engagement': 'engagement_score'}, inplace=True)
    logger.info(f"Engagement score range: {df['engagement_score'].min()} to {df['engagement_score'].max()}")
    
    # 4. Text preprocessing
    logger.info("Preprocessing text...")
    # Combine title and text if both exist
    if 'title' in df.columns and 'text' in df.columns:
        df['combined_text'] = df['title'].fillna('') + ' ' + df['text'].fillna('')
    else:
        df['combined_text'] = df['text'].fillna('')
    
    # Process text in chunks to avoid memory issues
    chunk_size = 1000
    total_rows = len(df)
    processed_texts = []
    
    for i in range(0, total_rows, chunk_size):
        chunk = df['combined_text'].iloc[i:i+chunk_size]
        processed_chunk = chunk.apply(lambda x: preprocess_text(x, remove_stopwords=True))
        processed_texts.extend(processed_chunk)
        logger.info(f"Processed {min(i+chunk_size, total_rows)}/{total_rows} texts")
    
    df['lemmatized_text'] = processed_texts
    logger.info(f"Data shape after text preprocessing: {df.shape}")
    
    # Log text preprocessing results
    empty_texts = df['lemmatized_text'].str.strip().eq('').sum()
    logger.info(f"Number of empty texts after preprocessing: {empty_texts}")
    
    # 5. Feature extraction
    logger.info("Extracting text features...")
    # Process features in chunks
    features_list = []
    for i in range(0, total_rows, chunk_size):
        chunk = df['lemmatized_text'].iloc[i:i+chunk_size]
        features_chunk = chunk.apply(extract_text_features)
        features_list.extend(features_chunk)
        logger.info(f"Extracted features for {min(i+chunk_size, total_rows)}/{total_rows} texts")
    
    features_df = pd.DataFrame(features_list)
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
    min_eng = df['engagement_score'].min()
    max_eng = df['engagement_score'].max()
    if max_eng > min_eng:
        df['normalized_engagement'] = (df['engagement_score'] - min_eng) / (max_eng - min_eng)
    else:
        df['normalized_engagement'] = 0
    
    # 8. Platform-specific features
    logger.info("Adding platform-specific features...")
    df['is_tiktok'] = (df['platform'] == 'tiktok').astype(int)
    df['is_reddit'] = (df['platform'] == 'reddit').astype(int)
    df['is_youtube'] = (df['platform'] == 'youtube').astype(int)
    
    # 9. Final cleaning
    logger.info("Performing final cleaning...")
    # Remove any remaining NaN values
    df = df.fillna({
        'word_count': 0,
        'char_count': 0,
        'avg_word_length': 0,
        'sentiment_score': 0,
        'sentiment_subjectivity': 0,
        'normalized_engagement': 0
    })
    
    # Select and reorder final columns
    final_columns = [
        'platform', 'content', 'engagement_score', 'normalized_engagement',
        'timestamp', 'hour', 'day_of_week', 'month', 'date',
        'word_count', 'char_count', 'avg_word_length',
        'sentiment_score', 'sentiment_subjectivity',
        'is_tiktok', 'is_reddit', 'is_youtube',
        'lemmatized_text'
    ]
    
    df = df[final_columns]
    logger.info(f"Final data shape: {df.shape}")
    logger.info(f"Final columns: {list(df.columns)}")
    
    return df 