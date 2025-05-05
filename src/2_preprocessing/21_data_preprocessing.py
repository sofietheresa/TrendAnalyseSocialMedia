import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
from textblob import TextBlob
import string
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002700-\U000027BF"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    return wordnet.NOUN

def lemmatize_tokens(tokens):
    tagged = pos_tag(tokens)
    lemmatizer = WordNetLemmatizer()
    return [lemmatizer.lemmatize(w, get_wordnet_pos(t)) for w, t in tagged]

def preprocess_text(text, remove_stopwords=True):
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = remove_emojis(text)
    text = re.sub(r'#(\w+)', r'\1', text)
    text = re.sub(r'[^\w\s\']', ' ', text)
    text = re.sub(r'\s\'|\'\s', ' ', text)
    text = ' '.join(text.split())

    tokens = word_tokenize(text, language='english')

    if remove_stopwords:
        stop_words = set()
        for lang in ['english', 'german']:
            try:
                stop_words.update(stopwords.words(lang))
            except:
                logger.warning(f"Stopwords for {lang} not available")
        stop_words = set(map(str.lower, stop_words))
        important_words = {"n't", "'s", "'m", "'re", "'ve", "'ll", "no", "not"}
        stop_words = stop_words - important_words

        tokens = [token for token in tokens if token.strip() and token.lower() not in stop_words]

    tokens = lemmatize_tokens(tokens)
    return ' '.join(tokens)

def extract_text_features(text):
    if not isinstance(text, str) or not text.strip():
        return {
            'word_count': 0,
            'char_count': 0,
            'avg_word_length': 0,
            'sentiment_polarity': 0,
            'sentiment_subjectivity': 0
        }

    words = text.split()
    word_count = len(words)
    char_count = len(text)
    avg_word_length = char_count / word_count if word_count > 0 else 0

    blob = TextBlob(text)
    return {
        'word_count': word_count,
        'char_count': char_count,
        'avg_word_length': avg_word_length,
        'sentiment_polarity': blob.sentiment.polarity,
        'sentiment_subjectivity': blob.sentiment.subjectivity
    }

def apply_text_processing(df, col):
    df[col] = df[col].astype(str).apply(lambda x: x.strip())
    df[f'{col}_processed'] = df[col].apply(preprocess_text)
    features = df[col].apply(extract_text_features)
    feature_df = pd.DataFrame(features.tolist())
    feature_df.columns = [f'{col}_{c}' for c in feature_df.columns]
    return pd.concat([df, feature_df], axis=1)

def load_data(raw_dir):
    paths = {
        "tiktok": raw_dir / "tiktok_data.csv",
        "youtube": raw_dir / "youtube_data.csv",
        "reddit": raw_dir / "reddit_data.csv"
    }
    return {name: pd.read_csv(path) for name, path in paths.items()}

def clean_tiktok_data(df):
    df = df.copy()
    text_cols = ['description', 'username']
    numeric_cols = ['likes', 'shares', 'comments', 'plays']

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in text_cols:
        if col in df.columns:
            df = apply_text_processing(df, col)

    try:
        numerator = df['likes'] + df['shares'] + df['comments']
        denominator = df['plays'].replace(0, np.nan)
        df['engagement_rate'] = (numerator / denominator).replace([np.inf, -np.inf], np.nan)
    except Exception as e:
        logger.warning(f"Could not calculate TikTok engagement rate: {e}")

    return df

def clean_youtube_data(df):
    df = df.copy()
    date_cols = ['published_at', 'scraped_at']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    numeric_cols = ['view_count', 'like_count', 'comment_count']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    text_cols = ['title', 'description', 'channel_title']
    for col in text_cols:
        if col in df.columns:
            df = apply_text_processing(df, col)

    try:
        numerator = df['like_count'] + df['comment_count']
        denominator = df['view_count'].replace(0, np.nan)
        df['engagement_rate'] = (numerator / denominator).replace([np.inf, -np.inf], np.nan)
    except Exception as e:
        logger.warning(f"Could not calculate YouTube engagement rate: {e}")

    return df

def clean_reddit_data(df):
    df = df.copy()
    relevant_cols = ['subreddit', 'title', 'text', 'score', 'comments', 'created', 'url']
    df = df[[col for col in relevant_cols if col in df.columns]]

    if 'created' in df.columns:
        df['created'] = pd.to_datetime(df['created'], errors='coerce')

    numeric_cols = ['score', 'comments']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    text_cols = ['title', 'text']
    for col in text_cols:
        if col in df.columns:
            df = apply_text_processing(df, col)

    try:
        numerator = df['comments']
        denominator = df['score'].replace(0, np.nan)
        df['engagement_rate'] = (numerator / denominator).replace([np.inf, -np.inf], np.nan)
    except Exception as e:
        logger.warning(f"Could not calculate Reddit engagement rate: {e}")

    return df

def normalize_metrics(df, columns):
    df = df.copy()
    existing_cols = [col for col in columns if col in df.columns]
    if existing_cols:
        df[existing_cols] = df[existing_cols].replace([np.inf, -np.inf], np.nan)
        for col in existing_cols:
            df[col] = df[col].fillna(df[col].mean())
        scaler = MinMaxScaler()
        df[existing_cols] = scaler.fit_transform(df[existing_cols])
    return df

def main():
    try:
        base_dir = Path(__file__).resolve().parent.parent.parent
    except NameError:
        base_dir = Path.cwd()

    raw_dir = base_dir / "data/raw"
    processed_dir = base_dir / "data/processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading data...")
    data = load_data(raw_dir)

    logger.info("Processing TikTok data...")
    data['tiktok'] = clean_tiktok_data(data['tiktok'])

    logger.info("Processing YouTube data...")
    data['youtube'] = clean_youtube_data(data['youtube'])

    logger.info("Processing Reddit data...")
    data['reddit'] = clean_reddit_data(data['reddit'])

    metrics = ['engagement_rate', 'sentiment_polarity', 'sentiment_subjectivity']
    for key in data:
        data[key] = normalize_metrics(data[key], metrics)
        data[key].to_csv(processed_dir / f"{key}_processed.csv", index=False)

    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()
