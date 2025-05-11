import sqlite3
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Konstanten
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data/social_media.db"
RAW_DIR = BASE_DIR / "data/raw"


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS reddit_data")
    cursor.execute("DROP TABLE IF EXISTS tiktok_data")
    cursor.execute("DROP TABLE IF EXISTS youtube_data")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reddit_data (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            score INTEGER,
            created_utc INTEGER,
            num_comments INTEGER,
            url TEXT,
            subreddit TEXT,
            scraped_at TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tiktok_data (
            id TEXT PRIMARY KEY,
            description TEXT,
            author_username TEXT,
            author_id TEXT,
            likes INTEGER,
            shares INTEGER,
            comments INTEGER,
            plays INTEGER,
            video_url TEXT,
            created_time INTEGER,
            scraped_at TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS youtube_data (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            channel_title TEXT,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            published_at TIMESTAMP,
            scraped_at TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    logging.info("✅ Datenbank-Tabellen erstellt")


def safe_int_convert(value):
    try:
        return int(float(value)) if value and str(value).strip() else 0
    except (ValueError, TypeError):
        return 0


def safe_str_convert(value):
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()


def safe_timestamp_convert(value):
    if pd.isna(value) or value is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
        return pd.to_datetime(value).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_leading_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    while df.shape[1] > 0 and df.iloc[:, 0].isna().all():
        df = df.iloc[:, 1:]
    return df


def import_reddit_data():
    try:
        # Lese die CSV-Datei und überspringe die erste Zeile
        df = pd.read_csv(RAW_DIR / "reddit_data.csv", skiprows=1)
        logging.info(f"Gelesene CSV-Datei hat {len(df)} Zeilen und {len(df.columns)} Spalten")
        
        # Extrahiere die Spaltennamen aus der ersten Zeile
        header_row = pd.read_csv(RAW_DIR / "reddit_data.csv", nrows=1)
        logging.info(f"Header-Zeile Spalten: {header_row.columns.tolist()}")
        
        # Nehme die letzten 8 Spalten und setze die korrekten Spaltennamen
        df = df.iloc[:, -8:]
        df.columns = ['subreddit', 'title', 'text', 'score', 'comments', 'created', 'url', 'scraped_at']
        
        # Debug-Ausgabe der ersten Zeile
        logging.info(f"Erste Zeile der Daten: {df.iloc[0].to_dict()}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        inserted_count = 0
        for index, row in df.iterrows():
            try:
                # Generiere eine eindeutige ID
                post_id = f"reddit_{index + 1}"
                
                # Extrahiere die Werte aus der Zeile
                title = safe_str_convert(row['title'])
                text = safe_str_convert(row['text'])
                score = safe_int_convert(row['score'])
                comments = safe_int_convert(row['comments'])
                
                # Konvertiere den created-Timestamp
                created_str = safe_str_convert(row['created'])
                try:
                    # Konvertiere den String in ein datetime-Objekt
                    dt = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S")
                    # Konvertiere in Unix-Timestamp (Sekunden seit 1970)
                    created = int(dt.timestamp())
                    # Debug-Ausgabe für die ersten 5 Einträge
                    if index < 5:
                        logging.info(f"Created (Rohwert): {created_str}")
                        logging.info(f"Created (konvertiert): {created} ({datetime.fromtimestamp(created)})")
                except Exception as e:
                    logging.warning(f"Fehler bei der Timestamp-Konvertierung in Zeile {index}: {e}")
                    created = int(datetime.now().timestamp())
                
                url = safe_str_convert(row['url'])
                subreddit = safe_str_convert(row['subreddit'])
                scraped_at = safe_timestamp_convert(row['scraped_at'])
                
                # Debug-Ausgabe für die ersten 5 Einträge
                if index < 5:
                    logging.info(f"Importiere Eintrag {index + 1}:")
                    logging.info(f"  Title: {title}")
                    logging.info(f"  Score: {score}")
                    logging.info(f"  Comments: {comments}")
                    logging.info(f"  Subreddit: {subreddit}")
                
                cursor.execute("""
                    INSERT OR REPLACE INTO reddit_data (
                        id, title, author, score, created_utc,
                        num_comments, url, subreddit, scraped_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_id,
                    title,
                    "",  # author ist nicht in den Daten vorhanden
                    score,
                    created,
                    comments,
                    url,
                    subreddit,
                    scraped_at
                ))
                inserted_count += 1
                
                if inserted_count % 100 == 0:
                    logging.info(f"Bisher {inserted_count} Einträge importiert")
                    
            except Exception as e:
                logging.warning(f"Fehler beim Import eines Reddit-Eintrags in Zeile {index}: {e}")
                continue

        conn.commit()
        conn.close()
        logging.info(f"✅ {inserted_count} Reddit-Einträge erfolgreich importiert")
        return inserted_count
    except Exception as e:
        logging.error(f"❌ Fehler beim Import der Reddit-Daten: {e}")
        return 0


def import_tiktok_data():
    try:
        df = pd.read_csv(RAW_DIR / "tiktok_data.csv", header=None)
        df = clean_leading_empty_columns(df)

        expected_cols = [
            'id', 'description', 'author_username', 'author_id',
            'likes', 'shares', 'comments', 'plays', 'video_url', 'created_time'
        ]

        df = df.iloc[:, :len(expected_cols)].copy()
        df.columns = expected_cols[:df.shape[1]]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO tiktok_data (
                    id, description, author_username, author_id,
                    likes, shares, comments, plays, video_url,
                    created_time, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                safe_str_convert(row.get('id', '')),
                safe_str_convert(row.get('description', '')),
                safe_str_convert(row.get('author_username', '')),
                safe_str_convert(row.get('author_id', '')),
                safe_int_convert(row.get('likes', 0)),
                safe_int_convert(row.get('shares', 0)),
                safe_int_convert(row.get('comments', 0)),
                safe_int_convert(row.get('plays', 0)),
                safe_str_convert(row.get('video_url', '')),
                safe_int_convert(row.get('created_time', 0)),
                safe_timestamp_convert(None)
            ))

        conn.commit()
        conn.close()
        logging.info(f"✅ {len(df)} TikTok-Einträge importiert")
        return len(df)

    except Exception as e:
        logging.error(f"❌ Fehler beim Import der TikTok-Daten: {e}")
        return 0


def import_youtube_data():
    try:
        df = pd.read_csv(RAW_DIR / "youtube_data.csv")
        df = clean_leading_empty_columns(df)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO youtube_data (
                    video_id, title, channel_title, view_count,
                    like_count, comment_count, published_at, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                safe_str_convert(row.get('video_id', '')),
                safe_str_convert(row.get('title', '')),
                safe_str_convert(row.get('channel_title', '')),
                safe_int_convert(row.get('view_count', 0)),
                safe_int_convert(row.get('like_count', 0)),
                safe_int_convert(row.get('comment_count', 0)),
                safe_timestamp_convert(row.get('published_at', None)),
                safe_timestamp_convert(row.get('scraped_at', None))
            ))

        conn.commit()
        conn.close()
        logging.info(f"✅ {len(df)} YouTube-Einträge importiert")
        return len(df)
    except Exception as e:
        logging.error(f"❌ Fehler beim Import der YouTube-Daten: {e}")
        return 0


def main():
    setup_database()
    reddit_count = import_reddit_data()
    tiktok_count = import_tiktok_data()
    youtube_count = import_youtube_data()

    logging.info("📊 Import-Statistiken:")
    logging.info(f"   Reddit: {reddit_count} Einträge")
    logging.info(f"   TikTok: {tiktok_count} Einträge")
    logging.info(f"   YouTube: {youtube_count} Einträge")
    logging.info(f"   Gesamt: {reddit_count + tiktok_count + youtube_count} Einträge")


if __name__ == "__main__":
    main()