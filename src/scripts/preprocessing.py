import logging
import os
from pathlib import Path

import pandas as pd
import numpy as np
from textblob import TextBlob
import emoji
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Setup logging
log_path = Path("logs/preprocessing.log")
log_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_data():
    """Load raw data from all platforms"""
    try:
        data = {}
        platforms = ['reddit', 'tiktok', 'youtube', 'twitter']
        
        for platform in platforms:
            file_path = f'data/raw/{platform}_data.csv'
            if os.path.exists(file_path):
                data[platform] = pd.read_csv(file_path)
                logging.info(f"Loaded {len(data[platform])} records from {platform}")
            else:
                logging.warning(f"No data file found for {platform}")
                
        return data
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        raise

def clean_text(text):
    """Clean and preprocess text data"""
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = ' '.join(word for word in text.split() if not word.startswith(('http://', 'https://')))
    
    # Remove special characters and numbers
    text = ''.join(char for char in text if char.isalpha() or char.isspace())
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def extract_emojis(text):
    """Extract emojis from text"""
    if not isinstance(text, str):
        return []
    return [c for c in text if c in emoji.EMOJI_DATA]

def get_sentiment(text):
    """Get sentiment score using TextBlob"""
    if not isinstance(text, str):
        return 0
    return TextBlob(text).sentiment.polarity

def preprocess_text(text):
    """Apply NLP preprocessing to text"""
    if not isinstance(text, str):
        return ""
    
    # Tokenize
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    return ' '.join(tokens)

def process_platform_data(df, platform):
    """Process data for a specific platform"""
    try:
        # Create a copy to avoid modifying the original
        processed_df = df.copy()
        
        # Platform-specific text columns
        text_columns = {
            'reddit': ['title', 'text'],
            'tiktok': ['desc'],
            'youtube': ['title', 'description'],
            'twitter': ['content']
        }
        
        # Process text columns
        for col in text_columns.get(platform, []):
            if col in processed_df.columns:
                # Clean text
                processed_df[f'{col}_cleaned'] = processed_df[col].apply(clean_text)
                
                # Extract emojis
                processed_df[f'{col}_emojis'] = processed_df[col].apply(extract_emojis)
                
                # Get sentiment
                processed_df[f'{col}_sentiment'] = processed_df[col].apply(get_sentiment)
                
                # Apply NLP preprocessing
                processed_df[f'{col}_processed'] = processed_df[col].apply(preprocess_text)
        
        # Add platform-specific features
        if platform == 'reddit':
            processed_df['engagement_score'] = processed_df['score']
        elif platform == 'tiktok':
            processed_df['engagement_score'] = processed_df['stats'].apply(
                lambda x: x.get('playCount', 0) + x.get('diggCount', 0) * 2
            )
        elif platform == 'youtube':
            processed_df['engagement_score'] = processed_df['viewCount'].astype(float) + \
                                             processed_df['likeCount'].astype(float) * 2
        elif platform == 'twitter':
            processed_df['engagement_score'] = processed_df['retweetCount'] + \
                                             processed_df['likeCount'] * 2
        
        return processed_df
        
    except Exception as e:
        logging.error(f"Error processing {platform} data: {str(e)}")
        raise

def main():
    """Main preprocessing function"""
    try:
        # Create processed data directory
        Path('data/processed').mkdir(parents=True, exist_ok=True)
        
        # Load raw data
        raw_data = load_data()
        
        # Process each platform's data
        for platform, df in raw_data.items():
            processed_df = process_platform_data(df, platform)
            
            # Save processed data
            output_path = f'data/processed/{platform}_processed.csv'
            processed_df.to_csv(output_path, index=False)
            logging.info(f"Saved processed data for {platform} to {output_path}")
        
        logging.info("Preprocessing completed successfully")
        
    except Exception as e:
        logging.error(f"Error in main preprocessing: {str(e)}")
        raise

if __name__ == "__main__":
    main() 