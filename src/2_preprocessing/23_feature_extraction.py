import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Konfigurierbarer Dateipfad
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data/processed"
INPUT_FILE = DATA_DIR / "cleaned_social_media_data.csv"
OUTPUT_FILE = DATA_DIR / "social_media_features.csv"

# Lade Daten
df = pd.read_csv(INPUT_FILE)

# Konvertiere Datumsspalten
df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
df['scraped_date'] = pd.to_datetime(df['scraped_date'], errors='coerce')

# Feature: Textlänge
df['text_length'] = df['text'].fillna('').apply(len)

# Feature: Wortanzahl
df['word_count'] = df['text'].fillna('').apply(lambda x: len(x.split()))

# Feature: Anzahl Hashtags
df['hashtag_count'] = df['text'].fillna('').apply(lambda x: x.count('#'))

# Feature: Anzahl Erwähnungen
df['mention_count'] = df['text'].fillna('').apply(lambda x: x.count('@'))

# Feature: Tageszeitkategorie
def get_day_period(hour):
    if pd.isna(hour):
        return np.nan
    if 5 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 17:
        return 'afternoon'
    elif 17 <= hour < 21:
        return 'evening'
    else:
        return 'night'

df['hour'] = df['created_date'].dt.hour
df['day_period'] = df['hour'].apply(get_day_period)

# Feature: Wochentag
df['weekday'] = df['created_date'].dt.day_name()

# Feature: Ist Wochenende
df['is_weekend'] = df['weekday'].isin(['Saturday', 'Sunday'])

# Feature: Jahr, Monat
df['year'] = df['created_date'].dt.year
df['month'] = df['created_date'].dt.month

# Fillna für views/likes/comments
for col in ['views', 'likes', 'comments']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Speichere als neue Datei
df.to_csv(OUTPUT_FILE, index=False)
print(f"Feature file saved to {OUTPUT_FILE}")
