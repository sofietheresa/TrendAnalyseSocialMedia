from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta
import urllib.parse
import logging
import sys

# Logging-Konfiguration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Start-Diagnose
logger.info("=== APPLICATION STARTING ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
logger.info(f"PORT: {os.getenv('PORT', '8000')}")

# FastAPI App
app = FastAPI(
    title="TrendAnalyseSocialMedia API",
    description="API zur Analyse von Social Media Trends",
    version="1.0.0"
)

# CORS-Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://trendanalysesocialmedia.vercel.app",
        "https://trendanalysesocialmedia-production.up.railway.app",
        "https://trendanalysesocialmedia-frontend.vercel.app",
        "*"  # Allow all origins temporarily for debugging
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton-Datenbankverbindung
db_engine = None

def get_db_connection():
    """Stelle eine Datenbankverbindung her oder verwende die bestehende"""
    try:
        global db_engine
        if db_engine is not None:
            # Überprüfe, ob die Verbindung noch aktiv ist
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.debug("Verwende bestehende Datenbankverbindung")
            return db_engine

        # Neue Verbindung herstellen
        url = os.getenv("DATABASE_URL")
        logger.info("Stelle neue Datenbankverbindung her")
        
        if not url:
            logger.error("DATABASE_URL Umgebungsvariable nicht gesetzt")
            raise ValueError("DATABASE_URL Umgebungsvariable nicht gesetzt")
        
        # Verbindung mit Optionen für bessere Stabilität
        db_engine = create_engine(
            url,
            pool_size=2,  # Reduzierte Pool-Größe
            max_overflow=5,
            pool_timeout=30,
            pool_recycle=1800,  # Verbindungen nach 30 Minuten recyceln
            connect_args={
                "connect_timeout": 10,
                "application_name": "trendanalyse-api"
            }
        )
        
        # Teste die Verbindung
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Datenbankverbindung erfolgreich hergestellt")
        
        return db_engine
    except Exception as e:
        logger.error(f"Fehler bei der Datenbankverbindung: {str(e)}")
        raise

# Diagnose-Endpunkte
@app.get("/")
async def root():
    """Basis-Endpunkt für Statusprüfung"""
    logger.info("Root-Endpunkt aufgerufen")
    return {
        "status": "online",
        "message": "TrendAnalyseSocialMedia API is running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detaillierter Gesundheitscheck mit DB-Verbindungsstatus"""
    logger.info("Health-Endpunkt aufgerufen")
    health_status = {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "application": "healthy",
            "database": "unknown"
        },
        "environment": os.getenv('FLASK_ENV', 'production'),
        "port": os.getenv('PORT', '8000')
    }
    
    # Optional: Versuche DB-Verbindung herzustellen
    try:
        db = get_db_connection()
        with db.connect() as conn:
            conn.execute(text("SELECT 1"))
            health_status["components"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Fehler beim Datenbank-Healthcheck: {str(e)}")
        health_status["components"]["database"] = "unhealthy"
        health_status["database_error"] = str(e)
    
    return health_status

@app.get("/info")
async def info():
    """Systeminformationen für Debugging"""
    logger.info("Info-Endpunkt aufgerufen")
    return {
        "python_version": sys.version,
        "environment": os.getenv('FLASK_ENV', 'production'),
        "port": os.getenv('PORT', '8000'),
        "working_directory": os.getcwd(),
        "timestamp": datetime.now().isoformat()
    }

# Hauptfunktionale Endpunkte
@app.get("/api/scraper-status")
async def get_scraper_status():
    """Liefert den Status der Scraper und die neuesten Daten"""
    logger.info("Scraper-Status-Endpunkt aufgerufen")
    
    try:
        db = get_db_connection()
        cutoff_time = datetime.now() - timedelta(minutes=20)
        
        status = {
            'reddit': {'running': False, 'total_posts': 0, 'last_update': None},
            'tiktok': {'running': False, 'total_posts': 0, 'last_update': None},
            'youtube': {'running': False, 'total_posts': 0, 'last_update': None}
        }
        
        # Tabellen, die überprüft werden sollen
        tables = [
            ('reddit_posts', 'reddit'),
            ('tiktok_posts', 'tiktok'),
            ('youtube_posts', 'youtube')
        ]
        
        with db.connect() as conn:
            # Überprüfe zuerst, ob die Tabellen existieren
            existing_tables = []
            try:
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('reddit_posts', 'tiktok_posts', 'youtube_posts')
                """))
                existing_tables = [row[0] for row in result]
                logger.info(f"Gefundene Tabellen: {existing_tables}")
            except Exception as e:
                logger.error(f"Fehler beim Überprüfen der Tabellenexistenz: {str(e)}")
            
            # Überprüfe jede Plattform
            for table_name, platform in tables:
                try:
                    if table_name not in existing_tables:
                        logger.warning(f"Tabelle {table_name} existiert nicht")
                        continue
                        
                    # Versuche alternative Abfrage, falls die Tabelle andere Namen hat
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*), MAX(scraped_at) FROM {table_name}"))
                        count, last_update = result.fetchone()
                        status[platform].update({
                            'running': last_update and last_update > cutoff_time,
                            'total_posts': count,
                            'last_update': last_update.isoformat() if last_update else None
                        })
                        logger.info(f"{platform.capitalize()} Status aktualisiert: {status[platform]}")
                    except Exception:
                        # Versuche Fallback mit dem alten Tabellennamen
                        alt_table = f"{platform}_data"
                        logger.warning(f"Versuche Fallback-Tabelle: {alt_table}")
                        result = conn.execute(text(f"SELECT COUNT(*), MAX(scraped_at) FROM {alt_table}"))
                        count, last_update = result.fetchone()
                        status[platform].update({
                            'running': last_update and last_update > cutoff_time,
                            'total_posts': count,
                            'last_update': last_update.isoformat() if last_update else None
                        })
                        logger.info(f"{platform.capitalize()} Status aktualisiert (Fallback): {status[platform]}")
                except Exception as e:
                    logger.error(f"Fehler beim Abrufen des {platform} Status: {str(e)}")
                    # Bei Fehlern einzelner Plattformen fortfahren
        
        return status
    except Exception as e:
        logger.error(f"Fehler im Scraper-Status-Endpunkt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/daily-stats")
async def get_daily_stats():
    """Liefert tägliche Statistiken für die letzten 7 Tage"""
    logger.info("Tägliche-Statistiken-Endpunkt aufgerufen")
    
    try:
        db = get_db_connection()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        stats = {
            'reddit': [],
            'tiktok': [],
            'youtube': []
        }
        
        # Tabellen, die überprüft werden sollen
        tables = [
            ('reddit_posts', 'reddit'),
            ('tiktok_posts', 'tiktok'),
            ('youtube_posts', 'youtube')
        ]
        
        with db.connect() as conn:
            # Überprüfe zuerst, ob die Tabellen existieren
            existing_tables = []
            try:
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('reddit_posts', 'tiktok_posts', 'youtube_posts')
                """))
                existing_tables = [row[0] for row in result]
                logger.info(f"Gefundene Tabellen: {existing_tables}")
            except Exception as e:
                logger.error(f"Fehler beim Überprüfen der Tabellenexistenz: {str(e)}")
            
            # Überprüfe jede Plattform
            for table_name, platform in tables:
                try:
                    if table_name not in existing_tables:
                        logger.warning(f"Tabelle {table_name} existiert nicht")
                        
                        # Versuche Fallback mit altem Tabellennamen
                        alt_table = f"{platform}_data"
                        logger.warning(f"Versuche Fallback-Tabelle: {alt_table}")
                        try:
                            query = text(f"""
                                SELECT DATE(scraped_at) as date, COUNT(*) as count
                                FROM {alt_table}
                                WHERE scraped_at >= :start_date
                                GROUP BY DATE(scraped_at)
                                ORDER BY date
                            """)
                            
                            result = conn.execute(query, {'start_date': start_date})
                            stats[platform] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
                            logger.info(f"{platform.capitalize()} Statistiken abgerufen (Fallback): {len(stats[platform])} Tage Daten")
                            continue
                        except Exception as e:
                            logger.error(f"Fallback für {platform} fehlgeschlagen: {str(e)}")
                            continue
                        
                    # Verwende den Standard-Tabellennamen
                    query = text(f"""
                        SELECT DATE(scraped_at) as date, COUNT(*) as count
                        FROM {table_name}
                        WHERE scraped_at >= :start_date
                        GROUP BY DATE(scraped_at)
                        ORDER BY date
                    """)
                    
                    result = conn.execute(query, {'start_date': start_date})
                    stats[platform] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
                    logger.info(f"{platform.capitalize()} Statistiken abgerufen: {len(stats[platform])} Tage Daten")
                except Exception as e:
                    logger.error(f"Fehler beim Abrufen der {platform} täglichen Statistiken: {str(e)}")
                    # Bei Fehlern einzelner Plattformen fortfahren
        
        return stats
    except Exception as e:
        logger.error(f"Fehler im Tägliche-Statistiken-Endpunkt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 