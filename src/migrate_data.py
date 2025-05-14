import logging
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from models import Base  # Importiere die Modelle

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lade Umgebungsvariablen
load_dotenv()

def migrate_to_railway():
    """Migriert Daten von SQLite zu Railway PostgreSQL"""
    try:
        # Railway Database URL
        target_db_url = os.getenv("DATABASE_URL")
        if not target_db_url:
            raise ValueError("DATABASE_URL nicht gefunden. Bitte in .env setzen!")

        # SQLite Quell-Datenbank
        source_db_url = "sqlite:///data/social_media.db"
        
        # Erstelle Engines für beide Datenbanken
        source_engine = create_engine(source_db_url)
        target_engine = create_engine(target_db_url)
        
        # Erstelle Tabellen in der Zieldatenbank
        logger.info("Erstelle Tabellen in der Zieldatenbank...")
        Base.metadata.create_all(target_engine)
        
        # Erstelle Sessions
        SourceSession = sessionmaker(bind=source_engine)
        TargetSession = sessionmaker(bind=target_engine)
        
        # Liste der zu migrierenden Tabellen
        tables_to_migrate = ['reddit_data', 'tiktok_data', 'youtube_data']
        
        # Migriere jede Tabelle
        for table_name in tables_to_migrate:
            logger.info(f"Migriere {table_name}...")
            
            # Metadata für die Quelltabelle
            source_metadata = MetaData()
            source_table = Table(table_name, source_metadata, autoload_with=source_engine)
            
            # Metadata für die Zieltabelle
            target_metadata = MetaData()
            target_table = Table(table_name, target_metadata, autoload_with=target_engine)
            
            source_session = SourceSession()
            target_session = TargetSession()
            
            try:
                # Lese Daten in Chunks
                chunk_size = 1000
                offset = 0
                total_migrated = 0
                
                while True:
                    # Hole nächsten Chunk
                    rows = source_session.query(source_table).limit(chunk_size).offset(offset).all()
                    if not rows:
                        break
                        
                    # Konvertiere zu Dictionary für einfacheres Einfügen
                    data = [dict(row._mapping) for row in rows]
                    
                    # Füge in Zieldatenbank ein
                    with target_engine.begin() as conn:
                        conn.execute(target_table.insert(), data)
                    
                    total_migrated += len(data)
                    offset += chunk_size
                    logger.info(f"✅ {total_migrated} Einträge für {table_name} migriert")
                
                target_session.commit()
                logger.info(f"Migration von {table_name} abgeschlossen!")
                
            except Exception as e:
                logger.error(f"Fehler bei der Migration von {table_name}: {str(e)}")
                target_session.rollback()
                raise
            finally:
                source_session.close()
                target_session.close()
        
        logger.info("Gesamte Migration erfolgreich abgeschlossen!")
        
    except Exception as e:
        logger.error(f"Fehler bei der Migration: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_to_railway() 