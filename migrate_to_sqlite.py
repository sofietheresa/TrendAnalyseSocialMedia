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


def get_existing_reddit_data(cursor):
    cursor.execute("SELECT * FROM reddit_data")
    columns = [description[0] for description in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=columns)


def get_existing_tiktok_data(cursor):
    cursor.execute("SELECT * FROM tiktok_data")
    columns = [description[0] for description in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=columns)


def get_existing_youtube_data(cursor):
    cursor.execute("SELECT * FROM youtube_data")
    columns = [description[0] for description in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=columns)


def import_reddit_data():
    try:
        # Lese die CSV-Datei und überspringe die erste Zeile
        df = pd.read_csv(RAW_DIR / "reddit_data.csv", skiprows=1)
        logging.info(f"Gelesene CSV-Datei hat {len(df)} Zeilen und {len(df.columns)} Spalten")
        
        # Nehme die letzten 8 Spalten und setze die korrekten Spaltennamen
        df = df.iloc[:, -8:]
        df.columns = ['subreddit', 'title', 'text', 'score', 'comments', 'created', 'url', 'scraped_at']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Hole existierende Daten
        existing_df = get_existing_reddit_data(cursor)
        
        inserted_count = 0
        updated_count = 0
        skipped_count = 0

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
                    dt = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S")
                    created = int(dt.timestamp())
                except Exception as e:
                    logging.warning(f"Fehler bei der Timestamp-Konvertierung in Zeile {index}: {e}")
                    created = int(datetime.now().timestamp())
                
                url = safe_str_convert(row['url'])
                subreddit = safe_str_convert(row['subreddit'])
                scraped_at = safe_timestamp_convert(row['scraped_at'])

                # Prüfe, ob der Eintrag bereits existiert
                existing_row = existing_df[existing_df['id'] == post_id]
                
                if len(existing_row) == 0:
                    # Neuer Eintrag
                    cursor.execute("""
                        INSERT INTO reddit_data (
                            id, title, author, score, created_utc,
                            num_comments, url, subreddit, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        post_id, title, "", score, created,
                        comments, url, subreddit, scraped_at
                    ))
                    inserted_count += 1
                else:
                    # Vergleiche die Werte
                    existing = existing_row.iloc[0]
                    if (existing['title'] != title or
                        existing['score'] != score or
                        existing['created_utc'] != created or
                        existing['num_comments'] != comments or
                        existing['url'] != url or
                        existing['subreddit'] != subreddit):
                        
                        # Update wenn sich etwas geändert hat
                        cursor.execute("""
                            UPDATE reddit_data SET
                                title = ?, score = ?, created_utc = ?,
                                num_comments = ?, url = ?, subreddit = ?,
                                scraped_at = ?
                            WHERE id = ?
                        """, (
                            title, score, created, comments,
                            url, subreddit, scraped_at, post_id
                        ))
                        updated_count += 1
                    else:
                        skipped_count += 1
                
                if (inserted_count + updated_count) % 100 == 0:
                    logging.info(f"Bisher {inserted_count} neue und {updated_count} aktualisierte Einträge")
                    
            except Exception as e:
                logging.warning(f"Fehler beim Import eines Reddit-Eintrags in Zeile {index}: {e}")
                continue

        conn.commit()
        conn.close()
        logging.info(f"✅ Reddit-Import abgeschlossen:")
        logging.info(f"   - {inserted_count} neue Einträge")
        logging.info(f"   - {updated_count} aktualisierte Einträge")
        logging.info(f"   - {skipped_count} unveränderte Einträge")
        return inserted_count + updated_count
    except Exception as e:
        logging.error(f"❌ Fehler beim Import der Reddit-Daten: {e}")
        return 0


def import_tiktok_data():
    try:
        df = pd.read_csv(RAW_DIR / "tiktok_data.csv")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Hole existierende Daten
        existing_df = get_existing_tiktok_data(cursor)
        
        inserted_count = 0
        updated_count = 0
        skipped_count = 0

        for index, row in df.iterrows():
            try:
                video_id = safe_str_convert(row.get('id', ''))
                if not video_id:
                    continue

                # Extrahiere die Werte
                description = safe_str_convert(row.get('description', ''))
                author_username = safe_str_convert(row.get('author_username', ''))
                author_id = safe_str_convert(row.get('author_id', ''))
                likes = safe_int_convert(row.get('likes', 0))
                shares = safe_int_convert(row.get('shares', 0))
                comments = safe_int_convert(row.get('comments', 0))
                plays = safe_int_convert(row.get('plays', 0))
                video_url = safe_str_convert(row.get('video_url', ''))
                created_time = safe_int_convert(row.get('created_time', 0))
                scraped_at = safe_timestamp_convert(None)

                # Prüfe, ob der Eintrag bereits existiert
                existing_row = existing_df[existing_df['id'] == video_id]
                
                if len(existing_row) == 0:
                    # Neuer Eintrag
                    cursor.execute("""
                        INSERT INTO tiktok_data (
                            id, description, author_username, author_id,
                            likes, shares, comments, plays, video_url,
                            created_time, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        video_id, description, author_username, author_id,
                        likes, shares, comments, plays, video_url,
                        created_time, scraped_at
                    ))
                    inserted_count += 1
                else:
                    # Vergleiche die Werte
                    existing = existing_row.iloc[0]
                    if (existing['description'] != description or
                        existing['author_username'] != author_username or
                        existing['author_id'] != author_id or
                        existing['likes'] != likes or
                        existing['shares'] != shares or
                        existing['comments'] != comments or
                        existing['plays'] != plays or
                        existing['video_url'] != video_url or
                        existing['created_time'] != created_time):
                        
                        # Update wenn sich etwas geändert hat
                        cursor.execute("""
                            UPDATE tiktok_data SET
                                description = ?, author_username = ?, author_id = ?,
                                likes = ?, shares = ?, comments = ?, plays = ?,
                                video_url = ?, created_time = ?, scraped_at = ?
                            WHERE id = ?
                        """, (
                            description, author_username, author_id,
                            likes, shares, comments, plays, video_url,
                            created_time, scraped_at, video_id
                        ))
                        updated_count += 1
                    else:
                        skipped_count += 1

                if (inserted_count + updated_count) % 100 == 0:
                    logging.info(f"Bisher {inserted_count} neue und {updated_count} aktualisierte Einträge")
                    
            except Exception as e:
                logging.warning(f"Fehler beim Import eines TikTok-Eintrags in Zeile {index}: {e}")
                continue

        conn.commit()
        conn.close()
        logging.info(f"✅ TikTok-Import abgeschlossen:")
        logging.info(f"   - {inserted_count} neue Einträge")
        logging.info(f"   - {updated_count} aktualisierte Einträge")
        logging.info(f"   - {skipped_count} unveränderte Einträge")
        return inserted_count + updated_count
    except Exception as e:
        logging.error(f"❌ Fehler beim Import der TikTok-Daten: {e}")
        return 0


def import_youtube_data():
    try:
        df = pd.read_csv(RAW_DIR / "youtube_data.csv")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Hole existierende Daten
        existing_df = get_existing_youtube_data(cursor)
        
        inserted_count = 0
        updated_count = 0
        skipped_count = 0

        for index, row in df.iterrows():
            try:
                video_id = safe_str_convert(row.get('video_id', ''))
                if not video_id:
                    continue

                # Extrahiere die Werte
                title = safe_str_convert(row.get('title', ''))
                channel_title = safe_str_convert(row.get('channel_title', ''))
                view_count = safe_int_convert(row.get('view_count', 0))
                like_count = safe_int_convert(row.get('like_count', 0))
                comment_count = safe_int_convert(row.get('comment_count', 0))
                published_at = safe_timestamp_convert(row.get('published_at', None))
                scraped_at = safe_timestamp_convert(row.get('scraped_at', None))

                # Prüfe, ob der Eintrag bereits existiert
                existing_row = existing_df[existing_df['video_id'] == video_id]
                
                if len(existing_row) == 0:
                    # Neuer Eintrag
                    cursor.execute("""
                        INSERT INTO youtube_data (
                            video_id, title, channel_title, view_count,
                            like_count, comment_count, published_at, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        video_id, title, channel_title, view_count,
                        like_count, comment_count, published_at, scraped_at
                    ))
                    inserted_count += 1
                else:
                    # Vergleiche die Werte
                    existing = existing_row.iloc[0]
                    if (existing['title'] != title or
                        existing['channel_title'] != channel_title or
                        existing['view_count'] != view_count or
                        existing['like_count'] != like_count or
                        existing['comment_count'] != comment_count or
                        existing['published_at'] != published_at):
                        
                        # Update wenn sich etwas geändert hat
                        cursor.execute("""
                            UPDATE youtube_data SET
                                title = ?, channel_title = ?, view_count = ?,
                                like_count = ?, comment_count = ?, published_at = ?,
                                scraped_at = ?
                            WHERE video_id = ?
                        """, (
                            title, channel_title, view_count,
                            like_count, comment_count, published_at,
                            scraped_at, video_id
                        ))
                        updated_count += 1
                    else:
                        skipped_count += 1

                if (inserted_count + updated_count) % 100 == 0:
                    logging.info(f"Bisher {inserted_count} neue und {updated_count} aktualisierte Einträge")
                    
            except Exception as e:
                logging.warning(f"Fehler beim Import eines YouTube-Eintrags in Zeile {index}: {e}")
                continue

        conn.commit()
        conn.close()
        logging.info(f"✅ YouTube-Import abgeschlossen:")
        logging.info(f"   - {inserted_count} neue Einträge")
        logging.info(f"   - {updated_count} aktualisierte Einträge")
        logging.info(f"   - {skipped_count} unveränderte Einträge")
        return inserted_count + updated_count
    except Exception as e:
        logging.error(f"❌ Fehler beim Import der YouTube-Daten: {e}")
        return 0


def main():
    setup_database()
    reddit_count = import_reddit_data()
    tiktok_count = import_tiktok_data()
    youtube_count = import_youtube_data()

    logging.info("📊 Import-Statistiken:")
    logging.info(f"   Reddit: {reddit_count} neue/aktualisierte Einträge")
    logging.info(f"   TikTok: {tiktok_count} neue/aktualisierte Einträge")
    logging.info(f"   YouTube: {youtube_count} neue/aktualisierte Einträge")
    logging.info(f"   Gesamt: {reddit_count + tiktok_count + youtube_count} neue/aktualisierte Einträge")


if __name__ == "__main__":
    main()