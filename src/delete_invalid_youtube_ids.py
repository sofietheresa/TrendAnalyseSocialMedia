import os
import psycopg2
import re
from dotenv import load_dotenv
import logging

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

def delete_invalid_youtube_ids():
    """Löscht Einträge mit ungültigen YouTube-IDs aus der Datenbank"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Zuerst die ungültigen IDs zählen
                cur.execute("""
                    SELECT COUNT(*) FROM public.youtube_data
                    WHERE video_id = 'status_update' OR 
                          video_id !~ '^[A-Za-z0-9_-]{11}$'
                """)
                invalid_count = cur.fetchone()[0]
                
                if invalid_count > 0:
                    print(f"Gefunden: {invalid_count} Einträge mit ungültigen IDs")
                    
                    # Dann die ungültigen Einträge löschen
                    cur.execute("""
                        DELETE FROM public.youtube_data
                        WHERE video_id = 'status_update' OR 
                              video_id !~ '^[A-Za-z0-9_-]{11}$'
                        RETURNING video_id;
                    """)
                    
                    deleted_ids = cur.fetchall()
                    conn.commit()
                    
                    print(f"✅ Erfolgreich {len(deleted_ids)} Einträge mit ungültigen IDs gelöscht.")
                    return len(deleted_ids)
                else:
                    print("Keine ungültigen YouTube-IDs gefunden.")
                    return 0
    except Exception as e:
        logger.error(f"Fehler beim Löschen ungültiger YouTube-IDs: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        deleted_count = delete_invalid_youtube_ids()
        print(f"Vorgang abgeschlossen. {deleted_count} Einträge wurden gelöscht.")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}") 