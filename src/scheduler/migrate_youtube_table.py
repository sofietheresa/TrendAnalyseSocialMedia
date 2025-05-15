import os
import psycopg2
import logging
from datetime import datetime
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Verbindung zur Hauptdatenbank herstellen"""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        logger.error(f"Datenbankverbindungsfehler: {str(e)}")
        raise

def migrate_youtube_table():
    """Migriert die YouTube-Tabelle, um trending_date hinzuzufügen und Primary Key zu ändern"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Prüfen, ob die Spalte trending_date bereits existiert
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'youtube_data' 
                    AND column_name = 'trending_date'
                """)
                
                column_exists = cur.fetchone() is not None
                
                if not column_exists:
                    logger.info("Spalte trending_date existiert nicht. Führe Migration durch...")
                    
                    # 1. Backup der Tabelle erstellen
                    cur.execute("CREATE TABLE youtube_data_backup AS SELECT * FROM youtube_data")
                    logger.info("Backup der YouTube-Tabelle erstellt")
                    
                    # 2. Anzahl der Datensätze im Backup zählen
                    cur.execute("SELECT COUNT(*) FROM youtube_data_backup")
                    backup_count = cur.fetchone()[0]
                    logger.info(f"Backup enthält {backup_count} Datensätze")
                    
                    # 3. trending_date Spalte hinzufügen und mit dem Datum des scraped_at befüllen
                    cur.execute("""
                        ALTER TABLE youtube_data 
                        ADD COLUMN trending_date DATE
                    """)
                    cur.execute("""
                        UPDATE youtube_data 
                        SET trending_date = DATE(scraped_at)
                    """)
                    
                    # 4. Primary Key entfernen und neu setzen
                    cur.execute("""
                        ALTER TABLE youtube_data 
                        DROP CONSTRAINT IF EXISTS youtube_data_pkey
                    """)
                    cur.execute("""
                        ALTER TABLE youtube_data 
                        ADD PRIMARY KEY (video_id, trending_date)
                    """)
                    
                    # 5. Prüfen, ob die Migration erfolgreich war
                    cur.execute("SELECT COUNT(*) FROM youtube_data")
                    new_count = cur.fetchone()[0]
                    
                    if new_count == backup_count:
                        logger.info(f"Migration erfolgreich: {new_count} Datensätze migriert")
                    else:
                        logger.warning(f"Migration möglicherweise unvollständig: {backup_count} in Backup, {new_count} in neuer Tabelle")
                    
                    conn.commit()
                    logger.info("Migration abgeschlossen")
                else:
                    logger.info("Spalte trending_date existiert bereits. Keine Migration erforderlich.")
                    
    except Exception as e:
        logger.error(f"Fehler bei der Migration: {str(e)}")
        logger.exception("Detaillierter Fehler:")
        raise

if __name__ == "__main__":
    try:
        migrate_youtube_table()
        print("✅ YouTube-Tabellenmigration erfolgreich abgeschlossen")
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {str(e)}") 