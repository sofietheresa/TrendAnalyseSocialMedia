import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
import logging
from datetime import datetime
import os
from models import get_db_url, init_db

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_data():
    """Migriert die Daten von SQLite nach PostgreSQL"""
    # SQLite-Datenbankpfad
    sqlite_path = Path("data/social_media.db")
    if not sqlite_path.exists():
        logger.error("SQLite-Datenbank nicht gefunden!")
        return

    try:
        # Verbindung zu SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        
        # Verbindung zu PostgreSQL
        postgres_url = get_db_url()
        postgres_engine = create_engine(postgres_url)
        
        # Initialisiere PostgreSQL-Tabellen
        init_db()
        
        # Migriere Tabelle für Tabelle
        tables = ['reddit_data', 'tiktok_data', 'youtube_data']
        
        for table in tables:
            logger.info(f"Migriere {table}...")
            
            # Lese Daten aus SQLite
            df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
            
            if not df.empty:
                # Konvertiere Zeitstempel
                if 'scraped_at' in df.columns:
                    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
                if 'published_at' in df.columns:
                    df['published_at'] = pd.to_datetime(df['published_at'])
                
                # Schreibe in PostgreSQL
                df.to_sql(
                    table,
                    postgres_engine,
                    if_exists='append',
                    index=False
                )
                
                logger.info(f"✅ {len(df)} Einträge für {table} migriert")
            else:
                logger.warning(f"Keine Daten in {table} gefunden")
        
        logger.info("Migration abgeschlossen!")
        
    except Exception as e:
        logger.error(f"Fehler bei der Migration: {str(e)}")
        raise
    finally:
        sqlite_conn.close()

if __name__ == "__main__":
    migrate_data() 