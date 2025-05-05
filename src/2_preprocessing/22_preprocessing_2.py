import os
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from datetime import datetime

# === NLTK Setup ===
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# === Dynamischer Datenpfad ===
BASE_DIR = os.getenv("DATA_DIR", "./data")
TIKTOK_FILE = os.path.join(BASE_DIR, "raw/tiktok_data.csv")
YOUTUBE_FILE = os.path.join(BASE_DIR, "raw/youtube_data.csv")
REDDIT_FILE = os.path.join(BASE_DIR, "raw/reddit_data.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "processed/cleaned_social_media_data.csv")

# === Preprocessing-Funktion ===
def preprocess_text(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", '', text, flags=re.MULTILINE)
    text = re.sub(r'\W+', ' ', text)
    tokens = nltk.word_tokenize(text)
    tokens = [t for t in tokens if t not in stopwords.words('english')]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(t) for t in tokens]
    return " ".join(tokens)

# === Helper-Funktion zur Datums-Spaltenerkennung ===
def find_and_parse_date(df, preferred_names):
    for name in preferred_names:
        for col in df.columns:
            if name.lower() in col.lower():
                print(f"✔️ Zeitspalte erkannt: {col}")
                return pd.to_datetime(df[col], errors='coerce')
    print("❌ Keine passende Zeitspalte gefunden.")
    return pd.NaT

# === TikTok-Daten ===
tiktok = pd.read_csv(TIKTOK_FILE)
tiktok_cleaned = pd.DataFrame({
    "source": "tiktok",
    "title": [None] * len(tiktok),
    "description/text": tiktok["description"].fillna(""),
    "author/channel": tiktok.get("author_username", None),
    "views/plays": tiktok.get("plays", None),
    "likes/score": tiktok.get("likes", None),
    "comments": tiktok.get("comments", None),
    "created date": find_and_parse_date(tiktok, ["created_time", "timestamp"]),
    "scraped date": [None] * len(tiktok)
})

# === YouTube-Daten ===
youtube = pd.read_csv(YOUTUBE_FILE)
youtube_cleaned = pd.DataFrame({
    "source": "youtube",
    "title": youtube["title"].fillna(""),
    "description/text": youtube["description"].fillna(""),
    "author/channel": youtube["channel_title"],
    "views/plays": youtube["view_count"],
    "likes/score": youtube["like_count"],
    "comments": youtube["comment_count"],
    "created date": find_and_parse_date(youtube, ["published_at"]),
    "scraped date": find_and_parse_date(youtube, ["scraped_at"])
})

# === Reddit-Daten ===
reddit = pd.read_csv(REDDIT_FILE)
reddit_cleaned = pd.DataFrame({
    "source": "reddit",
    "title": reddit["title"].fillna(""),
    "description/text": reddit["text"].fillna(""),
    "author/channel": reddit.get("author", reddit.get("subreddit", None)),
    "views/plays": [None] * len(reddit),
    "likes/score": reddit["score"],
    "comments": reddit["comments"],
    "created date": find_and_parse_date(reddit, ["created"]),
    "scraped date": find_and_parse_date(reddit, ["scraped_at"])
})

# === Zusammenführen ===
all_data = pd.concat([tiktok_cleaned, youtube_cleaned, reddit_cleaned], ignore_index=True)

# === Vorverarbeitung ===
all_data["title"] = all_data["title"].apply(preprocess_text)
all_data["description/text"] = all_data["description/text"].apply(preprocess_text)

# === Speichern ===
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
all_data.to_csv(OUTPUT_FILE, index=False)
print(f"✅ Datei '{OUTPUT_FILE}' wurde erfolgreich gespeichert.")
