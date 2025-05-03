import pandas as pd

# Reddit-Daten einlesen
df = pd.read_csv('data/raw/reddit_data.csv', 
                 encoding='utf-8',
                 usecols=['subreddit', 'title', 'text', 'score', 'comments', 'created', 'url', 'scraped_at'])

# Konvertiere Datumsspalten
df['created'] = pd.to_datetime(df['created'])
df['scraped_at'] = pd.to_datetime(df['scraped_at'])

# NaN-Werte entfernen
df = df.dropna(subset=['subreddit', 'title'])

# Erste Zeilen anzeigen
print("Erste 5 Zeilen der Daten:")
print(df.head())

# Info über den Datensatz
print("\nInformationen über den Datensatz:")
print(df.info()) 