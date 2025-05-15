from zenml.steps import step
import pandas as pd
import numpy as np
import re
import logging
from typing import List, Tuple
import importlib
import sys
import traceback

logger = logging.getLogger(__name__)

# Initialize dependencies with None
nltk = None
TextBlob = None
emoji = None
word_tokenize = None
stopwords = None
wordnet = None
WordNetLemmatizer = None
pos_tag = None

# Try to import required libraries
def setup_dependencies():
    """Install and import required dependencies"""
    global nltk, TextBlob, emoji, word_tokenize, stopwords, wordnet, WordNetLemmatizer, pos_tag
    
    try:
        import nltk
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords, wordnet
        from nltk.stem import WordNetLemmatizer
        from nltk import pos_tag
        
        # Download required NLTK data if not already downloaded
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
            
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet', quiet=True)
            
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger', quiet=True)
        
        logger.info("NLTK dependencies successfully imported and downloaded")
    except ImportError as e:
        logger.warning(f"Could not import NLTK: {str(e)}. Text processing will be limited.")
    
    try:
        from textblob import TextBlob
        logger.info("TextBlob successfully imported")
    except ImportError as e:
        logger.warning(f"Could not import TextBlob: {str(e)}. Sentiment analysis will be disabled.")
        TextBlob = None
    
    try:
        import emoji
        logger.info("Emoji successfully imported")
    except ImportError as e:
        logger.warning(f"Could not import emoji: {str(e)}. Emoji handling will be limited.")
        emoji = None

# Initialize dependencies
setup_dependencies()

def remove_emojis(text):
    """Remove emoji characters from text"""
    if not isinstance(text, str):
        return ""
    
    try:
        if emoji:
            return emoji.replace_emoji(text, replace='')
        else:
            # Simple regex fallback for emoji removal
            return re.sub(r'[^\x00-\x7F]+', '', text)
    except Exception as e:
        logger.warning(f"Error removing emojis: {str(e)}")
        return text

def get_wordnet_pos(tag):
    """Convert POS tag to WordNet POS tag format"""
    if not wordnet:
        return 'n'  # Default to noun if wordnet is not available
        
    try:
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
    except Exception as e:
        logger.warning(f"Error in POS tagging: {str(e)}")
        return wordnet.NOUN if wordnet else 'n'

def lemmatize_tokens(tokens):
    """Lemmatize tokens using POS tagging"""
    if not WordNetLemmatizer or not pos_tag:
        return tokens
        
    try:
        tagged = pos_tag(tokens)
        lemmatizer = WordNetLemmatizer()
        return [lemmatizer.lemmatize(w, get_wordnet_pos(t)) for w, t in tagged]
    except Exception as e:
        logger.warning(f"Error during lemmatization: {str(e)}")
        return tokens

def preprocess_text(text, remove_stopwords=True):
    """Preprocess text with various cleaning steps"""
    if not isinstance(text, str):
        return ""
    
    try:
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove emojis
        text = remove_emojis(text)
        
        # Remove special characters and numbers
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        
        # Return cleaned but unlemmatized text if NLTK is not available
        if not word_tokenize:
            return text.strip()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords if requested and available
        if remove_stopwords and stopwords:
            try:
                stop_words = set(stopwords.words('english'))
                tokens = [t for t in tokens if t not in stop_words]
            except Exception as e:
                logger.warning(f"Error removing stopwords: {str(e)}")
        
        # Lemmatize if possible
        if WordNetLemmatizer:
            tokens = lemmatize_tokens(tokens)
        
        return ' '.join(tokens)
    except Exception as e:
        logger.error(f"Error preprocessing text: {str(e)}")
        return "" if not isinstance(text, str) else text.lower()

def extract_text_features(text):
    """Extract numerical features from text"""
    if not isinstance(text, str) or not text.strip():
        return {
            'word_count': 0,
            'char_count': 0,
            'avg_word_length': 0,
            'sentiment_score': 0,
            'sentiment_subjectivity': 0
        }
    
    try:
        words = text.split()
        char_count = len(text)
        word_count = len(words)
        avg_word_length = char_count / word_count if word_count > 0 else 0
        
        sentiment_score = 0
        sentiment_subjectivity = 0
        
        # Calculate sentiment if TextBlob is available
        if TextBlob:
            try:
                blob = TextBlob(text)
                sentiment_score = blob.sentiment.polarity
                sentiment_subjectivity = blob.sentiment.subjectivity
            except Exception as e:
                logger.warning(f"Error in sentiment analysis: {str(e)}")
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'avg_word_length': avg_word_length,
            'sentiment_score': sentiment_score,
            'sentiment_subjectivity': sentiment_subjectivity
        }
    except Exception as e:
        logger.error(f"Error extracting text features: {str(e)}")
        return {
            'word_count': 0,
            'char_count': 0,
            'avg_word_length': 0,
            'sentiment_score': 0,
            'sentiment_subjectivity': 0
        }

@step
def preprocess_data(data: pd.DataFrame) -> pd.DataFrame:
    """Preprocess the social media data from the SQLite database."""
    logger.info(f"Starting preprocessing with input data shape: {data.shape}")
    
    try:
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # 1. Check for required columns
        required_columns = ['platform', 'content', 'engagement', 'timestamp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            # Create empty columns for missing ones
            for col in missing_columns:
                if col == 'timestamp':
                    df[col] = pd.NaT
                elif col == 'engagement':
                    df[col] = 0
                else:
                    df[col] = ''
            logger.info(f"Created empty columns for missing required columns")
        
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                logger.info("Converting timestamp column to datetime...")
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                null_timestamps = df['timestamp'].isnull().sum()
                if null_timestamps > 0:
                    logger.warning(f"Found {null_timestamps} invalid timestamps. These rows will be filled with current time.")
                    df.loc[df['timestamp'].isnull(), 'timestamp'] = pd.Timestamp.now()
        else:
            df['timestamp'] = pd.Timestamp.now()
            logger.warning("No timestamp column found, using current time for all rows")
        
        # 2. Basic cleaning
        logger.info("Performing basic cleaning...")
        df['text'] = df['content'].fillna('')
        logger.info(f"Data shape after basic cleaning: {df.shape}")
        
        # 3. Platform-specific processing
        logger.info("Performing platform-specific processing...")
        
        # TikTok specific
        tiktok_mask = df['platform'] == 'tiktok'
        if tiktok_mask.any():
            engagement_cols = [col for col in ['likes', 'shares', 'comments'] if col in df.columns]
            if engagement_cols:
                df.loc[tiktok_mask, 'engagement'] = df.loc[tiktok_mask, engagement_cols].fillna(0).sum(axis=1)
            else:
                logger.warning("No TikTok engagement columns found")
        
        # Reddit specific
        reddit_mask = df['platform'] == 'reddit'
        if reddit_mask.any():
            engagement_cols = [col for col in ['score', 'num_comments'] if col in df.columns]
            if engagement_cols:
                df.loc[reddit_mask, 'engagement'] = df.loc[reddit_mask, engagement_cols].fillna(0).sum(axis=1)
            else:
                logger.warning("No Reddit engagement columns found")
        
        # YouTube specific
        youtube_mask = df['platform'] == 'youtube'
        if youtube_mask.any():
            engagement_cols = [col for col in ['like_count', 'comment_count', 'view_count'] if col in df.columns]
            if engagement_cols:
                df.loc[youtube_mask, 'engagement'] = df.loc[youtube_mask, engagement_cols].fillna(0).sum(axis=1)
            else:
                logger.warning("No YouTube engagement columns found")
        
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
            # Use try/except to handle errors in each chunk
            try:
                processed_chunk = chunk.apply(lambda x: preprocess_text(x, remove_stopwords=True))
                processed_texts.extend(processed_chunk)
            except Exception as e:
                logger.error(f"Error processing text chunk {i}-{i+chunk_size}: {str(e)}")
                # Use simple lowercase as fallback
                processed_chunk = chunk.apply(lambda x: x.lower() if isinstance(x, str) else "")
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
            try:
                features_chunk = chunk.apply(extract_text_features)
                features_list.extend(features_chunk)
            except Exception as e:
                logger.error(f"Error extracting features from chunk {i}-{i+chunk_size}: {str(e)}")
                # Use empty features as fallback
                empty_features = [{
                    'word_count': 0,
                    'char_count': 0,
                    'avg_word_length': 0,
                    'sentiment_score': 0,
                    'sentiment_subjectivity': 0
                } for _ in range(len(chunk))]
                features_list.extend(empty_features)
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
            # Add default time features
            df['hour'] = 0
            df['day_of_week'] = 0
            df['month'] = 1
            df['date'] = pd.Timestamp.now().date()
        
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
        
        # Ensure all final columns exist
        for col in final_columns:
            if col not in df.columns:
                if col in ['date', 'timestamp']:
                    df[col] = pd.Timestamp.now()
                elif col in ['word_count', 'char_count', 'avg_word_length', 
                           'sentiment_score', 'sentiment_subjectivity', 
                           'hour', 'day_of_week', 'month',
                           'is_tiktok', 'is_reddit', 'is_youtube',
                           'engagement_score', 'normalized_engagement']:
                    df[col] = 0
                else:
                    df[col] = ''
        
        # Select only the columns we need
        available_columns = [col for col in final_columns if col in df.columns]
        df = df[available_columns]
        logger.info(f"Final data shape: {df.shape}")
        logger.info(f"Final columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error in preprocessing: {str(e)}")
        logger.error(traceback.format_exc())
        # Return a minimal dataframe with the required columns
        minimal_df = pd.DataFrame({
            'platform': ['unknown'],
            'content': [''],
            'engagement_score': [0],
            'normalized_engagement': [0],
            'timestamp': [pd.Timestamp.now()],
            'hour': [0],
            'day_of_week': [0],
            'month': [1],
            'date': [pd.Timestamp.now().date()],
            'word_count': [0],
            'char_count': [0],
            'avg_word_length': [0],
            'sentiment_score': [0],
            'sentiment_subjectivity': [0],
            'is_tiktok': [0],
            'is_reddit': [0],
            'is_youtube': [0],
            'lemmatized_text': ['']
        })
        return minimal_df 