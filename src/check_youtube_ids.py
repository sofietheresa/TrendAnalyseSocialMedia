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

def check_invalid_youtube_ids():
    """Identifiziert ungültige YouTube-IDs"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Hole alle Video-IDs und einige weitere Informationen
                cur.execute("""
                    SELECT video_id, title, published_at, scraped_at
                    FROM public.youtube_data
                    ORDER BY scraped_at DESC
                """)
                
                all_entries = cur.fetchall()
                invalid_entries = []
                
                # Regulärer Ausdruck für gültige YouTube-IDs (11 Zeichen, Buchstaben, Zahlen, Unterstrich, Bindestrich)
                valid_pattern = re.compile(r'^[A-Za-z0-9_-]{11}$')
                
                for entry in all_entries:
                    video_id = entry[0]
                    title = entry[1]
                    published_at = entry[2]
                    scraped_at = entry[3]
                    
                    # Prüfe, ob die ID ungültig ist
                    if video_id == "status_update" or not valid_pattern.match(video_id):
                        invalid_entries.append((video_id, title, published_at, scraped_at))
                
                # Zeige die ungültigen Einträge an
                if invalid_entries:
                    print(f"Gefunden: {len(invalid_entries)} Einträge mit ungültigen IDs:")
                    print("-" * 80)
                    for entry in invalid_entries:
                        video_id, title, published_at, scraped_at = entry
                        print(f"ID: {video_id}")
                        print(f"Titel: {title}")
                        print(f"Veröffentlicht: {published_at}")
                        print(f"Gescrapt: {scraped_at}")
                        print("-" * 80)
                else:
                    print("Keine ungültigen YouTube-IDs gefunden.")
                
                return invalid_entries
    except Exception as e:
        logger.error(f"Fehler beim Überprüfen der YouTube-IDs: {str(e)}")
        raise

def delete_invalid_youtube_ids():
    """Löscht Einträge mit ungültigen YouTube-IDs aus der Datenbank"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Regulärer Ausdruck für gültige YouTube-IDs (11 Zeichen, Buchstaben, Zahlen, Unterstrich, Bindestrich)
                cur.execute("""
                    DELETE FROM public.youtube_data
                    WHERE video_id = 'status_update' OR 
                          video_id !~ '^[A-Za-z0-9_-]{11}$'
                    RETURNING video_id;
                """)
                
                deleted_ids = cur.fetchall()
                conn.commit()
                
                if deleted_ids:
                    print(f"✅ Erfolgreich {len(deleted_ids)} Einträge mit ungültigen IDs gelöscht.")
                else:
                    print("Keine Einträge zum Löschen gefunden.")
                
                return len(deleted_ids)
    except Exception as e:
        logger.error(f"Fehler beim Löschen ungültiger YouTube-IDs: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        invalid_entries = check_invalid_youtube_ids()
        
        if invalid_entries:
            user_input = input(f"\nMöchten Sie diese {len(invalid_entries)} Einträge löschen? (ja/nein): ")
            if user_input.lower() in ('ja', 'j', 'yes', 'y'):
                deleted_count = delete_invalid_youtube_ids()
                print(f"Vorgang abgeschlossen. {deleted_count} Einträge wurden gelöscht.")
            else:
                print("Löschvorgang abgebrochen.")
        else:
            print("Keine Einträge zum Löschen gefunden.")
    except Exception as e:
        print(f"❌ Fehler: {str(e)}") 