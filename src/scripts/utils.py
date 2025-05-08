import re
import nltk
import string
import numpy as np
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
from sklearn.preprocessing import MinMaxScaler
from textblob import TextBlob
import logging
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("averaged_perceptron_tagger")

logger = logging.getLogger(__name__)

def detect_language(text):
    """
    Gibt Sprachcode zurück (z. B. 'en', 'de'), oder 'unknown' bei Fehlern.
    """
    try:
        return detect(text)
    except Exception:
        return "unknown"

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
    
    
    try:
        lang = detect(text)
    except Exception:
        return ""  # Sprache konnte nicht erkannt werden

    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = remove_emojis(text)
    text = re.sub(r"#(\w+)", r"\1", text)
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s'|'s", " ", text)
    text = ' '.join(text.split())

    tokens = word_tokenize(text, language='english')

    if remove_stopwords:
        stop_words = set()
        for lang in ['english', 'german']:
            try:
                stop_words.update(stopwords.words(lang))
            except:
                logger.warning(f"Stopwords für {lang} nicht verfügbar.")
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
