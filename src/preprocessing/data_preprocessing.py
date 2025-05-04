import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob
import string
from collections import defaultdict
import emoji

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

def preprocess_text(text, remove_stopwords=True):
    """
    Preprocess text data for NLP tasks.
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove emojis
    text = emoji.replace_emoji(text, '')
    
    # Handle hashtags - keep the text after #
    text = re.sub(r'#(\w+)', r'\1', text)
    
    # Remove special characters but keep apostrophes in words
    text = re.sub(r'[^\w\s\']', ' ', text)
    text = re.sub(r'\s\'|\'\s', ' ', text)  # Remove standalone apostrophes
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Tokenization
    tokens = word_tokenize(text)
    
    # Remove stopwords if specified
    if remove_stopwords:
        # Get stopwords for multiple languages
        stop_words = set()
        for lang in ['english', 'german']:
            try:
                stop_words.update(stopwords.words(lang))
            except:
                print(f"Warning: Stopwords for {lang} not available")
        
        # Keep contractions and meaningful short words
        important_words = {"n't", "'s", "'m", "'re", "'ve", "'ll", "no", "not"}
        stop_words = stop_words - important_words
        
        tokens = [token for token in tokens if token.strip() and token not in stop_words]
    
    # Lemmatization with proper POS tagging
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token, pos='v') for token in tokens]  # Verb lemmatization
    tokens = [lemmatizer.lemmatize(token, pos='n') for token in tokens]  # Noun lemmatization
    
    # Join tokens and remove extra whitespace
    text = ' '.join(tokens)
    text = ' '.join(text.split())
    
    return text

def extract_text_features(text):
    """
    Extract various text features for analysis.
    """
    if not isinstance(text, str) or not text.strip():
        return {
            'word_count': 0,
            'char_count': 0,
            'avg_word_length': 0,
            'sentiment_polarity': 0,
            'sentiment_subjectivity': 0
        }
    
    # Basic text statistics
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    avg_word_length = char_count / word_count if word_count > 0 else 0
    
    # Sentiment analysis using TextBlob
    blob = TextBlob(text)
    sentiment_polarity = blob.sentiment.polarity
    sentiment_subjectivity = blob.sentiment.subjectivity
    
    return {
        'word_count': word_count,
        'char_count': char_count,
        'avg_word_length': avg_word_length,
        'sentiment_polarity': sentiment_polarity,
        'sentiment_subjectivity': sentiment_subjectivity
    }

def load_data(raw_dir):
    """Load the raw data files."""
    tiktok_path = raw_dir / "tiktok_data.csv"
    youtube_path = raw_dir / "youtube_data.csv"
    reddit_path = raw_dir / "reddit_data.csv"
    
    print(f"Loading from paths:\n{tiktok_path}\n{youtube_path}\n{reddit_path}")
    
    df_tiktok = pd.read_csv(tiktok_path)
    df_youtube = pd.read_csv(youtube_path)
    df_reddit = pd.read_csv(reddit_path)
    
    return df_tiktok, df_youtube, df_reddit

def clean_tiktok_data(df):
    """Clean and preprocess TikTok data."""
    print("Original TikTok columns:", df.columns.tolist())
    df = df.copy()
    
    # Identify numeric columns based on content
    numeric_cols = []
    for col in df.columns:
        try:
            pd.to_numeric(df[col].iloc[0])
            numeric_cols.append(col)
        except (ValueError, TypeError):
            continue
    
    print("Identified numeric columns:", numeric_cols)
    
    # Convert numeric columns
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean and preprocess text columns
    text_cols = [col for col in df.columns if col not in numeric_cols]
    for col in text_cols:
        # Basic cleaning
        df[col] = df[col].astype(str).apply(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Text preprocessing for NLP
        df[f'{col}_processed'] = df[col].apply(preprocess_text)
        
        # Extract text features
        features = df[col].apply(extract_text_features)
        feature_df = pd.DataFrame(features.tolist())
        
        # Add prefix to feature columns
        feature_df.columns = [f'{col}_{col_name}' for col_name in feature_df.columns]
        
        # Add features to main dataframe
        df = pd.concat([df, feature_df], axis=1)
    
    # Add engagement metrics
    try:
        if all(col in numeric_cols for col in ['747600', '8890', '6626', '6600000']):
            numerator = df['747600'] + df['8890'] + df['6626']
            denominator = df['6600000'].replace(0, np.nan)
            df['engagement_rate'] = (numerator / denominator).replace([np.inf, -np.inf], np.nan)
    except Exception as e:
        print(f"Could not calculate engagement rate: {e}")
    
    return df

def clean_youtube_data(df):
    """Clean and preprocess YouTube data."""
    print("Original YouTube columns:", df.columns.tolist())
    df = df.copy()
    
    # Convert date columns
    date_cols = ['published_at', 'scraped_at']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Clean numeric columns
    numeric_cols = ['view_count', 'like_count', 'comment_count']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean and preprocess text columns
    text_cols = ['title', 'description', 'channel_title']
    for col in text_cols:
        if col in df.columns:
            # Basic cleaning
            df[col] = df[col].astype(str).apply(lambda x: x.strip() if isinstance(x, str) else x)
            
            # Text preprocessing for NLP
            df[f'{col}_processed'] = df[col].apply(preprocess_text)
            
            # Extract text features
            features = df[col].apply(extract_text_features)
            feature_df = pd.DataFrame(features.tolist())
            
            # Add prefix to feature columns
            feature_df.columns = [f'{col}_{col_name}' for col_name in feature_df.columns]
            
            # Add features to main dataframe
            df = pd.concat([df, feature_df], axis=1)
    
    # Add engagement metrics
    try:
        if all(col in df.columns for col in ['like_count', 'comment_count', 'view_count']):
            numerator = df['like_count'] + df['comment_count']
            denominator = df['view_count'].replace(0, np.nan)
            df['engagement_rate'] = (numerator / denominator).replace([np.inf, -np.inf], np.nan)
    except Exception as e:
        print(f"Could not calculate engagement rate: {e}")
    
    return df

def clean_reddit_data(df):
    """Clean and preprocess Reddit data."""
    print("Original Reddit columns:", df.columns.tolist())
    df = df.copy()
    
    # Keep only relevant columns
    relevant_cols = ['subreddit', 'title', 'text', 'score', 'comments', 'created', 'url']
    existing_cols = [col for col in relevant_cols if col in df.columns]
    df = df[existing_cols].copy()
    
    # Convert date columns
    if 'created' in df.columns:
        df['created'] = pd.to_datetime(df['created'], errors='coerce')
    
    # Clean numeric columns
    numeric_cols = ['score', 'comments']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean and preprocess text columns
    text_cols = ['title', 'text']
    for col in text_cols:
        if col in df.columns:
            # Basic cleaning
            df[col] = df[col].astype(str).apply(lambda x: x.strip() if isinstance(x, str) else x)
            
            # Text preprocessing for NLP
            df[f'{col}_processed'] = df[col].apply(preprocess_text)
            
            # Extract text features
            features = df[col].apply(extract_text_features)
            feature_df = pd.DataFrame(features.tolist())
            
            # Add prefix to feature columns
            feature_df.columns = [f'{col}_{col_name}' for col_name in feature_df.columns]
            
            # Add features to main dataframe
            df = pd.concat([df, feature_df], axis=1)
    
    # Add engagement metric
    try:
        if all(col in df.columns for col in ['comments', 'score']):
            numerator = df['comments']
            denominator = df['score'].replace(0, np.nan)
            df['engagement_rate'] = (numerator / denominator).replace([np.inf, -np.inf], np.nan)
    except Exception as e:
        print(f"Could not calculate engagement rate: {e}")
    
    return df

def normalize_metrics(df, columns):
    """Normalize numeric metrics using MinMaxScaler."""
    df = df.copy()
    existing_cols = [col for col in columns if col in df.columns]
    
    if existing_cols:
        # Replace infinite values with NaN
        df[existing_cols] = df[existing_cols].replace([np.inf, -np.inf], np.nan)
        
        # Fill NaN with mean of the column
        for col in existing_cols:
            df[col] = df[col].fillna(df[col].mean())
        
        # Apply scaling
        scaler = MinMaxScaler()
        df[existing_cols] = scaler.fit_transform(df[existing_cols])
    
    return df

def main():
    # Setup paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_dir = base_dir / "data/raw"
    processed_dir = base_dir / "data/processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Base directory: {base_dir}")
    print(f"Raw directory: {raw_dir}")
    print(f"Processed directory: {processed_dir}")
    
    # Load data
    print("\nLoading data...")
    df_tiktok, df_youtube, df_reddit = load_data(raw_dir)
    
    # Clean and preprocess data
    print("\nCleaning and preprocessing TikTok data...")
    df_tiktok_clean = clean_tiktok_data(df_tiktok)
    
    print("\nCleaning and preprocessing YouTube data...")
    df_youtube_clean = clean_youtube_data(df_youtube)
    
    print("\nCleaning and preprocessing Reddit data...")
    df_reddit_clean = clean_reddit_data(df_reddit)
    
    # Normalize metrics
    print("\nNormalizing metrics...")
    metrics_to_normalize = ['engagement_rate', 'sentiment_polarity', 'sentiment_subjectivity']
    df_tiktok_clean = normalize_metrics(df_tiktok_clean, metrics_to_normalize)
    df_youtube_clean = normalize_metrics(df_youtube_clean, metrics_to_normalize)
    df_reddit_clean = normalize_metrics(df_reddit_clean, metrics_to_normalize)
    
    # Save processed data
    print("\nSaving processed data...")
    df_tiktok_clean.to_csv(processed_dir / "tiktok_processed.csv", index=False)
    df_youtube_clean.to_csv(processed_dir / "youtube_processed.csv", index=False)
    df_reddit_clean.to_csv(processed_dir / "reddit_processed.csv", index=False)
    
    print("\nPreprocessing complete!")

if __name__ == "__main__":
    main() 