import requests
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
from pathlib import Path
import logging
from dotenv import load_dotenv
import json

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

API_URL = os.getenv("API_URL", "https://jpeg-merry-listing-combining.trycloudflare.com")
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
                platform_data = []
                for row in rows:
                    try:
                        item = dict(row)
                        # Timestamp-Konvertierung für JSON-Serialisierung
                        if 'scraped_at' in item and item['scraped_at']:
                            item['scraped_at'] = str(item['scraped_at'])
                        if 'created_utc' in item and item['created_utc']:
                            item['created_utc'] = int(item['created_utc'])
                        if 'published_at' in item and item['published_at']:
                            item['published_at'] = str(item['published_at'])
                        
                        item["platform"] = platform
                        platform_data.append(item)
                    except Exception as e:
                        logger.error(f"Fehler bei der Verarbeitung eines {platform}-Eintrags: {e}")
                        logger.error(f"Problematischer Eintrag: {row}")
                        continue
                
                logger.info(f"✓ {len(platform_data)} {platform}-Einträge geladen")
                all_data.extend(platform_data)
                
            except sqlite3.Error as e:
                logger.error(f"Datenbankfehler beim Laden von {table}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unerwarteter Fehler beim Laden von {table}: {e}")
                continue
        
        return all_data

    def sync_to_remote(self, data: List[Dict]) -> Dict:
        """Daten zum Remote-Server synchronisieren"""
        try:
            # Daten in kleinere Chunks aufteilen (max. 100 Einträge pro Request)
            chunk_size = 100
            chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
            
            total_stats = {"inserted": 0, "updated": 0, "errors": 0}
            
            for i, chunk in enumerate(chunks, 1):
                try:
                    logger.info(f"Sende Chunk {i}/{len(chunks)} ({len(chunk)} Einträge)...")
                    
                    # Validiere JSON-Serialisierung vor dem Senden
                    try:
                        json_data = json.dumps({"data": chunk})
                    except Exception as e:
                        logger.error(f"JSON-Serialisierungsfehler in Chunk {i}: {e}")
                        # Versuche problematische Einträge zu identifizieren
                        for entry in chunk:
                            try:
                                json.dumps(entry)
                            except Exception as e:
                                logger.error(f"Problematischer Eintrag: {entry}")
                                logger.error(f"Fehler: {e}")
                        continue
                    
                    response = requests.post(
                        f"{API_URL}/sync",
                        headers=HEADERS,
                        data=json_data,
                        timeout=30
                    )
                    
                    if response.status_code != 201:
                        logger.error(f"Unerwarteter Status-Code {response.status_code} für Chunk {i}")
                        logger.error(f"Server-Antwort: {response.text}")
                        continue
                        
                    result = response.json()
                    chunk_stats = result.get('stats', {})
                    
                    # Aktualisiere Gesamtstatistik
                    total_stats["inserted"] += chunk_stats.get("inserted", 0)
                    total_stats["updated"] += chunk_stats.get("updated", 0)
                    total_stats["errors"] += chunk_stats.get("errors", 0)
                    
                    logger.info(f"✓ Chunk {i} verarbeitet: "
                              f"{chunk_stats.get('inserted', 0)} eingefügt, "
                              f"{chunk_stats.get('updated', 0)} aktualisiert, "
                              f"{chunk_stats.get('errors', 0)} Fehler")
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Netzwerkfehler bei Chunk {i}: {e}")
                    if hasattr(e.response, 'text'):
                        logger.error(f"Server-Antwort: {e.response.text}")
                    total_stats["errors"] += len(chunk)
                    continue
                except Exception as e:
                    logger.error(f"Unerwarteter Fehler bei Chunk {i}: {e}")
                    total_stats["errors"] += len(chunk)
                    continue
            
            return {
                "status": "success" if total_stats["errors"] == 0 else "partial_success",
                "message": "Synchronisation abgeschlossen",
                "stats": total_stats
            }
            
        except Exception as e:
            logger.error(f"Kritischer Fehler bei der Synchronisation: {e}")
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
        logger.info(" Lokale Datenbankstatistiken:")
        stats_before = db.get_local_stats()
        for table, count in stats_before.items():
            logger.info(f"  {table}: {count}")
        
        # Lokale Daten abrufen und zum Server synchronisieren
        logger.info(" Starte Datensynchronisation zum Server...")
        local_data = db.fetch_local_data()
        
        if not local_data:
            logger.warning(" Keine lokalen Daten zum Synchronisieren gefunden")
            return
            
        logger.info(f" Sende {len(local_data)} Datensätze zum Server...")
        sync_result = db.sync_to_remote(local_data)
        
        # Detaillierte Ergebnisausgabe
        logger.info("\n=== Synchronisationsergebnis ===")
        logger.info(f"Status: {sync_result.get('status')}")
        logger.info(f"Nachricht: {sync_result.get('message')}")
        
        if 'stats' in sync_result:
            stats = sync_result['stats']
            logger.info("\nStatistik:")
            logger.info(f"   Neue Einträge: {stats.get('inserted', 0)}")
            logger.info(f"   Aktualisierte Einträge: {stats.get('updated', 0)}")
            logger.info(f"   Fehler: {stats.get('errors', 0)}")
            
            if stats.get('errors', 0) > 0:
                logger.warning("\n Es sind Fehler aufgetreten! Bitte überprüfen Sie das Log für Details.")
            
    except Exception as e:
        logger.error(f" Kritischer Fehler während der Synchronisation: {e}", exc_info=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()