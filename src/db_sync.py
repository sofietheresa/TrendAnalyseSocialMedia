import requests
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
from pathlib import Path
import logging
from dotenv import load_dotenv

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/db_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === KONFIGURATION ===
load_dotenv()

API_URL = os.getenv("API_URL", "https://composed-gzip-license-agriculture.trycloudflare.com")
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY muss in .env gesetzt sein!")

DB_PATH = Path("data/social_media.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"X-API-Key": API_KEY}

# === TABELLENSTRUKTUR ===
CREATE_TABLES = {
    "reddit_data": """
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
    """,
    "tiktok_data": """
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
    """,
    "youtube_data": """
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
    """
}

class DatabaseSync:
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.conn = None
        self.ensure_db_exists()

    def ensure_db_exists(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        for table_name, ddl in CREATE_TABLES.items():
            cursor.execute(ddl)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_scraped 
                ON {table_name}(scraped_at)
            """)
        self.conn.commit()

    def fetch_remote_data(self, endpoint: str = "/data") -> List[Dict]:
        try:
            response = requests.get(f"{API_URL}{endpoint}", headers=HEADERS)
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"API-Anfrage fehlgeschlagen: {e}")
            raise

    def upload_to_server(self, data: List[Dict]):
        try:
            response = requests.post(f"{API_URL}/sync", json={"data": data}, headers=HEADERS)
            response.raise_for_status()
            logger.info(f"{len(data)} lokale Einträge an Server gesendet.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler beim Upload an Server: {e}")

    def get_local_stats(self) -> Dict[str, int]:
        stats = {}
        cursor = self.conn.cursor()
        for table in CREATE_TABLES.keys():
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()["count"]
            cursor.execute(f"SELECT MAX(scraped_at) as latest FROM {table}")
            latest = cursor.fetchone()["latest"]
            stats[f"{table}_latest"] = latest if latest else "Keine Daten"
        return stats

    def insert_or_update_data(self, data: List[Dict]) -> Dict[str, int]:
        stats = {"inserted": 0, "updated": 0, "errors": 0}
        cursor = self.conn.cursor()

        for item in data:
            platform = item.get("platform")
            try:
                if platform == "reddit":
                    cursor.execute("""
                        INSERT OR REPLACE INTO reddit_data 
                        (id, title, text, author, score, created_utc, num_comments, url, subreddit, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.get("id"), item.get("title"), item.get("text"),
                        item.get("author"), item.get("score"), item.get("created_utc"),
                        item.get("num_comments"), item.get("url"), item.get("subreddit"),
                        item.get("scraped_at")
                    ))

                elif platform == "tiktok":
                    cursor.execute("""
                        INSERT OR REPLACE INTO tiktok_data 
                        (id, description, author_username, author_id, likes, shares, comments, plays, video_url, created_time, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.get("id"), item.get("description"), item.get("author_username"),
                        item.get("author_id"), item.get("likes"), item.get("shares"),
                        item.get("comments"), item.get("plays"), item.get("video_url"),
                        item.get("created_time"), item.get("scraped_at")
                    ))

                elif platform == "youtube":
                    cursor.execute("""
                        INSERT OR REPLACE INTO youtube_data 
                        (video_id, title, description, channel_title, view_count, like_count, comment_count, published_at, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.get("video_id"), item.get("title"), item.get("description"),
                        item.get("channel_title"), item.get("view_count"), item.get("like_count"),
                        item.get("comment_count"), item.get("published_at"), item.get("scraped_at")
                    ))

                stats["inserted"] += 1

            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von {platform}-Daten: {e}")
                stats["errors"] += 1

        self.conn.commit()
        return stats

    def export_unsynced_data(self, platform: str, since: str) -> List[Dict]:
        cursor = self.conn.cursor()
        query = f"SELECT * FROM {platform}_data WHERE scraped_at > ?"
        cursor.execute(query, (since,))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()

def main():
    try:
        db = DatabaseSync()

        logger.info("Lokale Datenbankstatistiken vor Sync:")
        stats_before = db.get_local_stats()
        for table, count in stats_before.items():
            logger.info(f"  {table}: {count}")

        logger.info("Starte Datensynchronisation...")
        remote_data = db.fetch_remote_data()
        db.insert_or_update_data(remote_data)

        for platform in ["reddit", "tiktok", "youtube"]:
            latest = stats_before.get(f"{platform}_data_latest")
            if latest and latest != "Keine Daten":
                unsynced = db.export_unsynced_data(platform, latest)
                if unsynced:
                    logger.info(f"Sende {len(unsynced)} {platform}-Einträge an Server...")
                    db.upload_to_server(unsynced)

        logger.info("Synchronisation abgeschlossen:")
        stats_after = db.get_local_stats()
        for table, count in stats_after.items():
            logger.info(f"  {table}: {count}")

    except Exception as e:
        logger.error(f"Fehler während der Synchronisation: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()