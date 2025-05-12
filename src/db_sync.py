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

API_URL = os.getenv("API_URL", "http://localhost:8000")
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
        """Stellt sicher, dass die Datenbank und Tabellen existieren"""
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

    def fetch_local_data(self) -> List[Dict]:
        """Lokale Daten aus der Datenbank abrufen"""
        all_data = []
        cursor = self.conn.cursor()
        
        for platform, table in {
            "reddit": "reddit_data",
            "tiktok": "tiktok_data",
            "youtube": "youtube_data"
        }.items():
            try:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                for row in rows:
                    item = dict(row)
                    item["platform"] = platform
                    all_data.append(item)
            except sqlite3.Error as e:
                logger.warning(f"Fehler beim Laden von {table}: {e}")
                continue
        
        return all_data

    def sync_to_remote(self, data: List[Dict]) -> Dict:
        """Daten zum Remote-Server synchronisieren"""
        try:
            response = requests.post(
                f"{API_URL}/sync",
                headers=HEADERS,
                json={"data": data},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Fehler bei der Remote-Synchronisation: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Server-Antwort: {e.response.text}")
            raise

    def get_local_stats(self) -> Dict[str, int]:
        """Statistiken über lokale Daten abrufen"""
        stats = {}
        cursor = self.conn.cursor()
        
        for table in CREATE_TABLES.keys():
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()["count"]
            
            cursor.execute(f"SELECT MAX(scraped_at) as latest FROM {table}")
            latest = cursor.fetchone()["latest"]
            stats[f"{table}_latest"] = latest if latest else "Keine Daten"
        
        return stats

    def close(self):
        """Datenbankverbindung schließen"""
        if self.conn:
            self.conn.close()

def main():
    try:
        db = DatabaseSync()
        
        # Aktuelle Statistiken anzeigen
        logger.info("📊 Lokale Datenbankstatistiken:")
        stats_before = db.get_local_stats()
        for table, count in stats_before.items():
            logger.info(f"  {table}: {count}")
        
        # Lokale Daten abrufen und zum Server synchronisieren
        logger.info("🔄 Starte Datensynchronisation zum Server...")
        local_data = db.fetch_local_data()
        logger.info(f"📤 Sende {len(local_data)} Datensätze zum Server...")
        
        if local_data:
            sync_result = db.sync_to_remote(local_data)
            logger.info("✅ Synchronisation abgeschlossen:")
            logger.info(f"  Status: {sync_result.get('status')}")
            logger.info(f"  Nachricht: {sync_result.get('message')}")
            if 'stats' in sync_result:
                stats = sync_result['stats']
                logger.info(f"  Neue Einträge: {stats.get('inserted', 0)}")
                logger.info(f"  Aktualisierte Einträge: {stats.get('updated', 0)}")
                logger.info(f"  Fehler: {stats.get('errors', 0)}")
        else:
            logger.warning("⚠️ Keine lokalen Daten zum Synchronisieren gefunden")
            
    except Exception as e:
        logger.error(f"❌ Fehler während der Synchronisation: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()