import os
import psycopg2
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

def add_url_column():
    """Fügt eine neue URL-Spalte zur youtube_data-Tabelle hinzu"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Prüfe, ob die Spalte bereits existiert
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'youtube_data' AND column_name = 'url'
                """)
                
                if cur.fetchone():
                    logger.info("Die Spalte 'url' existiert bereits in der youtube_data-Tabelle.")
                else:
                    # Füge die URL-Spalte hinzu
                    cur.execute("""
                        ALTER TABLE public.youtube_data 
                        ADD COLUMN IF NOT EXISTS url TEXT
                    """)
                    logger.info("Die Spalte 'url' wurde erfolgreich zur youtube_data-Tabelle hinzugefügt.")
                
                # Aktualisiere alle Einträge ohne URL
                cur.execute("""
                    UPDATE public.youtube_data 
                    SET url = 'https://www.youtube.com/watch?v=' || video_id 
                    WHERE url IS NULL OR url = ''
                """)
                
                updated_rows = cur.rowcount
                conn.commit()
                
                logger.info(f"{updated_rows} Einträge mit YouTube-URLs aktualisiert.")
                
                return updated_rows
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der YouTube-URLs: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        rows_updated = add_url_column()
        print(f"✅ URL-Spalte hinzugefügt und {rows_updated} Einträge aktualisiert.")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}") 