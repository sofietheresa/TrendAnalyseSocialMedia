import logging
import os
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Konstanten
BASE_DIR = Path(__file__).resolve().parent
DB_PATH =  Path("data")  / "social_media.db"
RAW_DIR =  Path("data")  / "raw"


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reddit_data (
            id TEXT PRIMARY KEY,
            title TEXT,
            text TEXT,
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
            description TEXT,
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


def delete_source_file(file_path):
    try:
        if file_path.exists():
            file_path.unlink()
            logging.info(f"✅ Quelldatei gelöscht: {file_path}")
    except Exception as e:
        logging.error(f"❌ Fehler beim Löschen der Quelldatei {file_path}: {e}")


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


def get_csv_files(prefix):
    """Findet alle CSV-Dateien mit dem angegebenen Präfix im RAW_DIR."""
    try:
        files = list(RAW_DIR.glob(f"{prefix}_*.csv"))
        if not files:
            # Fallback für Dateien ohne Unterstrich
            files = list(RAW_DIR.glob(f"{prefix}*.csv"))
        return files
    except Exception as e:
        logging.error(f"Fehler beim Suchen von {prefix}-CSV-Dateien: {e}")
        return []


def import_reddit_data():
    try:
        logging.info("Starte Reddit-Import...")
        csv_files = get_csv_files("reddit")
        if not csv_files:
            logging.warning("Keine Reddit-CSV-Dateien gefunden")
            return 0

        total_inserted = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0

        for csv_path in csv_files:
            logging.info(f"Verarbeite Reddit-Datei: {csv_path}")
            try:
                # Lese die CSV-Datei und überspringe die erste Zeile
                df = pd.read_csv(csv_path, skiprows=1)
                logging.info(f"Gelesene CSV-Datei hat {len(df)} Zeilen und {len(df.columns)} Spalten")
                logging.info(f"Spalten: {df.columns.tolist()}")
                
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
                error_count = 0

                for index, row in df.iterrows():
                    try:
                        # Generiere eine eindeutige ID basierend auf URL und Timestamp
                        url = safe_str_convert(row['url'])
                        if not url:
                            logging.warning(f"Keine URL in Zeile {index}")
                            error_count += 1
                            continue
                            
                        # Extrahiere die Post-ID aus der URL oder generiere eine eindeutige ID
                        post_id = None
                        if url:
                            # Versuche die ID aus der URL zu extrahieren
                            url_parts = url.split('/')
                            if len(url_parts) > 1:
                                post_id = url_parts[-1]
                        
                        # Wenn keine ID aus der URL extrahiert werden konnte, generiere eine eindeutige ID
                        if not post_id:
                            # Erstelle eine eindeutige ID aus URL und Timestamp
                            timestamp = safe_str_convert(row['created'])
                            unique_string = f"{url}_{timestamp}_{index}"
                            post_id = hashlib.md5(unique_string.encode()).hexdigest()
                        
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
                        
                        subreddit = safe_str_convert(row['subreddit'])
                        scraped_at = safe_timestamp_convert(row['scraped_at'])

                        # Prüfe, ob der Eintrag bereits existiert
                        existing_row = existing_df[existing_df['id'] == post_id]
                        
                        if len(existing_row) == 0:
                            # Neuer Eintrag
                            cursor.execute("""
                                INSERT INTO reddit_data (
                                    id, title, text, author, score, created_utc,
                                    num_comments, url, subreddit, scraped_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                post_id, title, text, "", score, created,
                                comments, url, subreddit, scraped_at
                            ))
                            inserted_count += 1
                        else:
                            # Vergleiche die Werte
                            existing = existing_row.iloc[0]
                            if (existing['title'] != title or
                                existing['text'] != text or
                                existing['score'] != score or
                                existing['created_utc'] != created or
                                existing['num_comments'] != comments or
                                existing['url'] != url or
                                existing['subreddit'] != subreddit):
                                
                                # Update wenn sich etwas geändert hat
                                cursor.execute("""
                                    UPDATE reddit_data SET
                                        title = ?, text = ?, score = ?, created_utc = ?,
                                        num_comments = ?, url = ?, subreddit = ?,
                                        scraped_at = ?
                                    WHERE id = ?
                                """, (
                                    title, text, score, created, comments,
                                    url, subreddit, scraped_at, post_id
                                ))
                                updated_count += 1
                            else:
                                skipped_count += 1
                        
                    except Exception as e:
                        logging.warning(f"Fehler beim Import eines Reddit-Eintrags in Zeile {index}: {e}")
                        error_count += 1
                        continue

                conn.commit()
                conn.close()

                total_inserted += inserted_count
                total_updated += updated_count
                total_skipped += skipped_count
                total_errors += error_count

                logging.info(f"✅ Reddit-Import für {csv_path} abgeschlossen:")
                logging.info(f"   - {inserted_count} neue Einträge")
                logging.info(f"   - {updated_count} aktualisierte Einträge")
                logging.info(f"   - {skipped_count} unveränderte Einträge")
                logging.info(f"   - {error_count} fehlerhafte Einträge")

                # Lösche die verarbeitete Datei
                delete_source_file(csv_path)

            except Exception as e:
                logging.error(f"❌ Fehler beim Verarbeiten der Reddit-Datei {csv_path}: {e}")
                continue

        logging.info(f"📊 Gesamtstatistik Reddit-Import:")
        logging.info(f"   - {total_inserted} neue Einträge")
        logging.info(f"   - {total_updated} aktualisierte Einträge")
        logging.info(f"   - {total_skipped} unveränderte Einträge")
        logging.info(f"   - {total_errors} fehlerhafte Einträge")
        return total_inserted + total_updated

    except Exception as e:
        logging.error(f"❌ Fehler beim Import der Reddit-Daten: {e}")
        return 0


def import_tiktok_data():
    try:
        logging.info("Starte TikTok-Import...")
        csv_files = get_csv_files("tiktok")
        if not csv_files:
            logging.warning("Keine TikTok-CSV-Dateien gefunden")
            return 0

        total_inserted = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0

        for csv_path in csv_files:
            logging.info(f"Verarbeite TikTok-Datei: {csv_path}")
            try:
                df = pd.read_csv(csv_path)
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Hole existierende Daten
                existing_df = get_existing_tiktok_data(cursor)
                
                inserted_count = 0
                updated_count = 0
                skipped_count = 0
                error_count = 0

                for index, row in df.iterrows():
                    try:
                        video_id = safe_str_convert(row.get('id', ''))
                        if not video_id:
                            error_count += 1
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
                        scraped_at = safe_timestamp_convert(row.get('scraped_at', None))

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

                    except Exception as e:
                        logging.warning(f"Fehler beim Import eines TikTok-Eintrags in Zeile {index}: {e}")
                        error_count += 1
                        continue

                conn.commit()
                conn.close()

                total_inserted += inserted_count
                total_updated += updated_count
                total_skipped += skipped_count
                total_errors += error_count

                logging.info(f"✅ TikTok-Import für {csv_path} abgeschlossen:")
                logging.info(f"   - {inserted_count} neue Einträge")
                logging.info(f"   - {updated_count} aktualisierte Einträge")
                logging.info(f"   - {skipped_count} unveränderte Einträge")
                logging.info(f"   - {error_count} fehlerhafte Einträge")

                # Lösche die verarbeitete Datei
                delete_source_file(csv_path)

            except Exception as e:
                logging.error(f"❌ Fehler beim Verarbeiten der TikTok-Datei {csv_path}: {e}")
                continue

        logging.info(f"📊 Gesamtstatistik TikTok-Import:")
        logging.info(f"   - {total_inserted} neue Einträge")
        logging.info(f"   - {total_updated} aktualisierte Einträge")
        logging.info(f"   - {total_skipped} unveränderte Einträge")
        logging.info(f"   - {total_errors} fehlerhafte Einträge")
        return total_inserted + total_updated

    except Exception as e:
        logging.error(f"❌ Fehler beim Import der TikTok-Daten: {e}")
        return 0


def import_youtube_data():
    try:
        logging.info("Starte YouTube-Import...")
        csv_files = get_csv_files("youtube")
        if not csv_files:
            logging.warning("Keine YouTube-CSV-Dateien gefunden")
            return 0

        total_inserted = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0

        for csv_path in csv_files:
            logging.info(f"Verarbeite YouTube-Datei: {csv_path}")
            try:
                df = pd.read_csv(csv_path)
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                # Hole existierende Daten
                existing_df = get_existing_youtube_data(cursor)
                
                inserted_count = 0
                updated_count = 0
                skipped_count = 0
                error_count = 0

                for index, row in df.iterrows():
                    try:
                        video_id = safe_str_convert(row.get('video_id', ''))
                        if not video_id:
                            error_count += 1
                            continue

                        # Extrahiere die Werte
                        title = safe_str_convert(row.get('title', ''))
                        description = safe_str_convert(row.get('description', ''))
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
                                    video_id, title, description, channel_title, view_count,
                                    like_count, comment_count, published_at, scraped_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                video_id, title, description, channel_title, view_count,
                                like_count, comment_count, published_at, scraped_at
                            ))
                            inserted_count += 1
                        else:
                            # Vergleiche die Werte
                            existing = existing_row.iloc[0]
                            if (existing['title'] != title or
                                existing['description'] != description or
                                existing['channel_title'] != channel_title or
                                existing['view_count'] != view_count or
                                existing['like_count'] != like_count or
                                existing['comment_count'] != comment_count or
                                existing['published_at'] != published_at):
                                
                                # Update wenn sich etwas geändert hat
                                cursor.execute("""
                                    UPDATE youtube_data SET
                                        title = ?, description = ?, channel_title = ?, view_count = ?,
                                        like_count = ?, comment_count = ?, published_at = ?,
                                        scraped_at = ?
                                    WHERE video_id = ?
                                """, (
                                    title, description, channel_title, view_count,
                                    like_count, comment_count, published_at,
                                    scraped_at, video_id
                                ))
                                updated_count += 1
                            else:
                                skipped_count += 1

                    except Exception as e:
                        logging.warning(f"Fehler beim Import eines YouTube-Eintrags in Zeile {index}: {e}")
                        error_count += 1
                        continue

                conn.commit()
                conn.close()

                total_inserted += inserted_count
                total_updated += updated_count
                total_skipped += skipped_count
                total_errors += error_count

                logging.info(f"✅ YouTube-Import für {csv_path} abgeschlossen:")
                logging.info(f"   - {inserted_count} neue Einträge")
                logging.info(f"   - {updated_count} aktualisierte Einträge")
                logging.info(f"   - {skipped_count} unveränderte Einträge")
                logging.info(f"   - {error_count} fehlerhafte Einträge")

                # Lösche die verarbeitete Datei
                delete_source_file(csv_path)

            except Exception as e:
                logging.error(f"❌ Fehler beim Verarbeiten der YouTube-Datei {csv_path}: {e}")
                continue

        logging.info(f"📊 Gesamtstatistik YouTube-Import:")
        logging.info(f"   - {total_inserted} neue Einträge")
        logging.info(f"   - {total_updated} aktualisierte Einträge")
        logging.info(f"   - {total_skipped} unveränderte Einträge")
        logging.info(f"   - {total_errors} fehlerhafte Einträge")
        return total_inserted + total_updated

    except Exception as e:
        logging.error(f"❌ Fehler beim Import der YouTube-Daten: {e}")
        return 0


def clean_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Lösche Reddit-Einträge ohne ID
        cursor.execute("DELETE FROM reddit_data WHERE id IS NULL OR id = ''")
        reddit_deleted = cursor.rowcount
        
        # Lösche TikTok-Einträge ohne ID
        cursor.execute("DELETE FROM tiktok_data WHERE id IS NULL OR id = ''")
        tiktok_deleted = cursor.rowcount
        
        # Lösche YouTube-Einträge ohne ID
        cursor.execute("DELETE FROM youtube_data WHERE video_id IS NULL OR video_id = ''")
        youtube_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logging.info("✅ Datenbank bereinigt:")
        logging.info(f"   - {reddit_deleted} Reddit-Einträge ohne ID gelöscht")
        logging.info(f"   - {tiktok_deleted} TikTok-Einträge ohne ID gelöscht")
        logging.info(f"   - {youtube_deleted} YouTube-Einträge ohne ID gelöscht")
        
    except Exception as e:
        logging.error(f"❌ Fehler beim Bereinigen der Datenbank: {e}")


def main():
    logging.info("Starte Import-Prozess...")
    setup_database()
    
    # Bereinige die Datenbank vor dem Import
    clean_database()
    
    logging.info("Starte Reddit-Import...")
    reddit_count = import_reddit_data()
    if reddit_count > 0:
        delete_source_file(RAW_DIR / "reddit_data.csv")
    
    logging.info("Starte TikTok-Import...")
    tiktok_count = import_tiktok_data()
    if tiktok_count > 0:
        delete_source_file(RAW_DIR / "tiktok_data.csv")
    
    logging.info("Starte YouTube-Import...")
    youtube_count = import_youtube_data()
    if youtube_count > 0:
        delete_source_file(RAW_DIR / "youtube_data.csv")

    logging.info("📊 Import-Statistiken:")
    logging.info(f"   Reddit: {reddit_count} neue/aktualisierte Einträge")
    logging.info(f"   TikTok: {tiktok_count} neue/aktualisierte Einträge")
    logging.info(f"   YouTube: {youtube_count} neue/aktualisierte Einträge")
    logging.info(f"   Gesamt: {reddit_count + tiktok_count + youtube_count} neue/aktualisierte Einträge")


if __name__ == "__main__":
    main()