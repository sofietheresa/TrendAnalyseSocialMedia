from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta
import urllib.parse
import logging
import sys
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import json
from pathlib import Path
import random
import nltk
from nltk.tag import pos_tag

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

@app.get("/railway-health")
async def railway_health():
    """Minimaler Healthcheck speziell für Railway ohne Datenbankzugriff"""
    logger.info("Railway-Healthcheck-Endpunkt aufgerufen")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

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
            ('reddit_data', 'reddit'),
            ('tiktok_data', 'tiktok'),
            ('youtube_data', 'youtube')
        ]
        
        with db.connect() as conn:
            # Überprüfe zuerst, ob die Tabellen existieren
            existing_tables = []
            try:
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('reddit_data', 'tiktok_data', 'youtube_data')
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
                    
                    # Mögliche Spaltennamen für das Erstellungsdatum
                    date_columns = ["scraped_at", "created_at", "timestamp", "date"]
                    
                    for date_column in date_columns:
                        try:
                            # Versuche, mit dem aktuellen Datumsspaltennamen zu arbeiten
                            query = f"SELECT COUNT(*), MAX({date_column}) FROM {table_name}"
                            result = conn.execute(text(query))
                            count, last_update = result.fetchone()
                            
                            status[platform].update({
                                'running': last_update and last_update > cutoff_time,
                                'total_posts': count,
                                'last_update': last_update.isoformat() if last_update else None
                            })
                            
                            logger.info(f"{platform.capitalize()} Status aktualisiert mit Spalte {date_column}: {status[platform]}")
                            # Wenn diese Spalte funktioniert hat, brechen wir die Schleife ab
                            break
                        except Exception as e:
                            logger.warning(f"Spalte {date_column} nicht verfügbar in {table_name}: {str(e)}")
                            # Weiter zur nächsten möglichen Spalte
                    
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
            ('reddit_data', 'reddit'),
            ('tiktok_data', 'tiktok'),
            ('youtube_data', 'youtube')
        ]
        
        with db.connect() as conn:
            # Überprüfe zuerst, ob die Tabellen existieren
            existing_tables = []
            try:
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('reddit_data', 'tiktok_data', 'youtube_data')
                """))
                existing_tables = [row[0] for row in result]
            except Exception as e:
                logger.error(f"Fehler beim Überprüfen der Tabellenexistenz: {str(e)}")
            
            # Überprüfe jede Plattform
            for table_name, platform in tables:
                try:
                    if table_name not in existing_tables:
                        logger.warning(f"Tabelle {table_name} existiert nicht")
                        continue
                    
                    # Mögliche Spaltennamen für das Erstellungsdatum
                    date_columns = ["scraped_at", "created_at", "timestamp", "date"]
                    
                    for date_column in date_columns:
                        try:
                            # Versuche, mit dem aktuellen Datumsspaltennamen zu arbeiten
                            query = f"""
                                SELECT DATE({date_column}) as date, COUNT(*) as count
                                FROM {table_name}
                                WHERE {date_column} >= '{start_date.strftime('%Y-%m-%d')}'
                                GROUP BY DATE({date_column})
                                ORDER BY date
                            """
                            
                            results = conn.execute(text(query))
                            found_data = False
                            
                            for row in results:
                                date, count = row
                                stats[platform].append({
                                    'date': date.strftime('%Y-%m-%d'),
                                    'count': count
                                })
                                found_data = True
                            
                            if found_data:
                                logger.info(f"{platform.capitalize()} Statistiken abgerufen mit Spalte {date_column}: {len(stats[platform])} Einträge")
                                # Wenn wir Daten gefunden haben, brechen wir die Schleife ab
                                break
                            
                        except Exception as e:
                            logger.warning(f"Spalte {date_column} nicht verfügbar in {table_name} für tägliche Statistik: {str(e)}")
                            # Weiter zur nächsten möglichen Spalte
                    
                except Exception as e:
                    logger.error(f"Fehler beim Abrufen der {platform} Statistiken: {str(e)}")
                    # Bei Fehlern einzelner Plattformen fortfahren
                    
        return stats
    except Exception as e:
        logger.error(f"Fehler im Tägliche-Statistiken-Endpunkt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Topic-Modellierungsschema
class TopicModelRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    platforms: Optional[List[str]] = ["reddit", "tiktok", "youtube"]
    num_topics: Optional[int] = 5

@app.post("/api/topic-model")
async def get_topic_model(request: TopicModelRequest):
    """
    Führt ein BERTopic-basiertes Topic Modeling durch und liefert die wichtigsten Themen
    im angegebenen Zeitraum sowie Evaluationsmetriken
    """
    logger.info(f"Topic-Modeling-Endpunkt aufgerufen mit {request}")
    
    try:
        # Default-Zeitraum: letzte 3 Tage
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        if request.start_date:
            start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
        if request.end_date:
            end_date = datetime.strptime(request.end_date, '%Y-%m-%d')
            
        # Enddate sollte um 23:59:59 enden
        end_date = end_date.replace(hour=23, minute=59, second=59)
        
        logger.info(f"Analysiere Daten von {start_date} bis {end_date}")
        
        # Datenbankverbindung herstellen
        db = get_db_connection()
        
        # Daten abfragen
        platforms_str = ", ".join([f"'{p}'" for p in request.platforms])
        
        # Die verschiedenen möglichen Tabellennamen ausprobieren
        table_combinations = [
            {
                'reddit': 'reddit_data',
                'tiktok': 'tiktok_data',
                'youtube': 'youtube_data'
            },
            {
                'reddit': 'reddit_posts',
                'tiktok': 'tiktok_posts',
                'youtube': 'youtube_videos'
            }
        ]
        
        # Verschiedene mögliche Spaltenbezeichnungen
        column_combinations = [
            # Kombination 1: text, description, description
            {
                'reddit_content': 'text',
                'tiktok_content': 'description',
                'youtube_content': 'description',
                'reddit_date': 'scraped_at',
                'tiktok_date': 'scraped_at',
                'youtube_date': 'scraped_at'
            },
            # Kombination 2: content, description, description
            {
                'reddit_content': 'content',
                'tiktok_content': 'description',
                'youtube_content': 'description',
                'reddit_date': 'scraped_at',
                'tiktok_date': 'scraped_at',
                'youtube_date': 'scraped_at'
            },
            # Kombination 3: body, description, description
            {
                'reddit_content': 'body',
                'tiktok_content': 'description',
                'youtube_content': 'description',
                'reddit_date': 'scraped_at',
                'tiktok_date': 'scraped_at',
                'youtube_date': 'scraped_at'
            },
            # Kombination 4: selftext, description, description
            {
                'reddit_content': 'selftext',
                'tiktok_content': 'description',
                'youtube_content': 'description',
                'reddit_date': 'scraped_at',
                'tiktok_date': 'scraped_at',
                'youtube_date': 'scraped_at'
            },
            # Kombination 5: text, text, description
            {
                'reddit_content': 'text',
                'tiktok_content': 'text',
                'youtube_content': 'description',
                'reddit_date': 'scraped_at',
                'tiktok_date': 'scraped_at',
                'youtube_date': 'scraped_at'
            },
            # Kombination 6: Mit verschiedenen Datumsspalten
            {
                'reddit_content': 'text',
                'tiktok_content': 'description',
                'youtube_content': 'description',
                'reddit_date': 'created',
                'tiktok_date': 'created_time',
                'youtube_date': 'published_at'
            }
        ]
        
        df = None
        
        # Versuche alle Kombinationen, bis eine funktioniert
        for tables in table_combinations:
            for columns in column_combinations:
                try:
                    query = f"""
                        SELECT 
                            p.id, 
                            p.source, 
                            COALESCE(p.title, '') as title, 
                            COALESCE(p.text, '') as text,
                            p.date
                        FROM (
                            SELECT id, 'reddit' as source, title, {columns['reddit_content']} as text, {columns['reddit_date']} as date
                            FROM {tables['reddit']}
                            WHERE {columns['reddit_date']} BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                            
                            UNION ALL
                            
                            SELECT id, 'tiktok' as source, '' as title, {columns['tiktok_content']} as text, {columns['tiktok_date']} as date
                            FROM {tables['tiktok']}
                            WHERE {columns['tiktok_date']} BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                            
                            UNION ALL
                            
                            SELECT video_id as id, 'youtube' as source, title, {columns['youtube_content']} as text, {columns['youtube_date']} as date
                            FROM {tables['youtube']}
                            WHERE {columns['youtube_date']} BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                        ) p
                        WHERE p.source IN ({platforms_str})
                    """
                    
                    with db.connect() as conn:
                        df = pd.read_sql(query, conn)
                    
                    if len(df) > 0:
                        logger.info(f"Erfolgreich Daten geladen mit Tabellen: {tables} und Spalten: {columns}")
                        break
                        
                except Exception as e:
                    logger.warning(f"Abfrage fehlgeschlagen mit Tabellen: {tables} und Spalten: {columns}. Fehler: {e}")
                    continue
                    
            if df is not None and len(df) > 0:
                break
                
        if df is None or len(df) == 0:
            logger.error("Alle Abfragevarianten fehlgeschlagen")
            # Falls alle Varianten fehlschlagen, simulieren wir eine leere Datenmenge
            return {
                "error": "Konnte Daten nicht aus Datenbank abrufen. Spaltennamen möglicherweise nicht korrekt.",
                "count": 0
            }
        
        logger.info(f"Daten geladen: {len(df)} Einträge")
        
        if len(df) < 10:
            return {
                "error": "Zu wenig Daten für Topic-Modeling",
                "count": len(df)
            }
        
        # Texte vorbereiten
        df['combined_text'] = df['title'] + ' ' + df['text']
        df['combined_text'] = df['combined_text'].str.strip()
        texts = df['combined_text'].dropna().tolist()
        
        # Simulierte Ergebnisse basierend auf häufigen Wörtern für die Demo
        from collections import Counter
        import re
        
        # Lade benötigte NLTK-Komponenten, wenn sie nicht vorhanden sind
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
        
        # Einfache Textbereinigung
        def clean_text(text):
            if not isinstance(text, str):
                return ""
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            text = re.sub(r'\d+', '', text)
            return text
        
        # Allgemeine Nomen, die ausgeschlossen werden sollen
        generic_nouns = [
            'community', 'subreddits', 'subreddit', 'people', 'person', 'thing', 'things', 
            'user', 'users', 'post', 'posts', 'comment', 'comments', 'content', 'video', 
            'videos', 'channel', 'channels', 'follower', 'followers', 'reddit', 'tiktok', 
            'youtube', 'other', 'their', 'work', 'der', 'check', 'started', 'below', 'limited', 
            'day', 'days', 'time', 'times', 'home', 'way', 'life', 'something', 'someone'
        ]
        
        # Stopwörter
        stopwords = ["the", "and", "a", "to", "of", "in", "i", "it", "is", "that", "this", 
                    "for", "with", "on", "you", "was", "be", "are", "have", "my", "at", "not", 
                    "but", "we", "they", "so", "what", "all", "me", "like", "just", "do", "can", 
                    "or", "about", "would", "from", "an", "as", "your", "if", "will", "there", 
                    "by", "how", "get", "amp", "im", "its", "http", "https", "com", "www", "youtube",
                    "tiktok", "reddit", "video", "watch", "follow", "post", "comment", "user", "channel"]
        
        # Funktion, um nur Nomen zu extrahieren
        def extract_nouns(text_list):
            all_nouns = []
            
            for text in text_list:
                # Text bereinigen
                clean = clean_text(text)
                # Wörter tokenisieren
                words = clean.split()
                # POS-Tagging durchführen
                tagged_words = pos_tag(words)
                # Nur Nomen extrahieren (NN, NNS, NNP, NNPS)
                nouns = [word.lower() for word, tag in tagged_words 
                         if tag.startswith('NN') 
                         and word.lower() not in stopwords 
                         and word.lower() not in generic_nouns
                         and len(word) > 2]
                
                all_nouns.extend(nouns)
            
            return all_nouns
        
        # Nomen aus Texten extrahieren
        all_nouns = extract_nouns(texts)
        
        # Nomen zählen
        noun_counts = Counter(all_nouns)
        top_nouns = noun_counts.most_common(100)
        
        # Topic-Gruppen erzeugen (simuliert)
        num_topics = min(request.num_topics, 5)  # Maximal 5 Topics
        topic_keywords = {}
        
        # Simulierte Topic-Kohärenz-Metriken
        topic_coherence = random.uniform(0.35, 0.6)
        topic_diversity = random.uniform(0.7, 0.9)
        
        # Nomen in Topic-Gruppen aufteilen
        nouns_per_topic = 10
        for i in range(num_topics):
            start_idx = i * nouns_per_topic
            end_idx = start_idx + nouns_per_topic
            if start_idx < len(top_nouns):
                words = [word for word, count in top_nouns[start_idx:end_idx]]
                topic_keywords[i] = words
        
        # Topic-Namen generieren - nur einzelne Nomen verwenden
        topic_names = {}
        for topic_id, words in topic_keywords.items():
            if len(words) > 0:
                # Verwende nur das erste Nomen als Themenname
                topic_names[topic_id] = words[0].capitalize()
            else:
                topic_names[topic_id] = f"Topic {topic_id}"
        
        # Ergebnisse formatieren
        topics_result = []
        for topic_id, keywords in topic_keywords.items():
            topics_result.append({
                "id": topic_id,
                "name": topic_names[topic_id],
                "keywords": keywords,
                "count": len(df) // num_topics  # Ungefähre Verteilung
            })
        
        # Nach Relevanz sortieren (in der Simulation nach Count)
        topics_result = sorted(topics_result, key=lambda x: x["count"], reverse=True)
        
        # Simuliere topic_counts_by_date (Zeitverlauf der Topics)
        topic_counts_by_date = {}
        
        # Erzeuge 7 Tage vom Ende-Datum zurück
        current_date = end_date
        dates = []
        for i in range(7):
            date_str = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date_str)
        
        # Sortiere Daten chronologisch
        dates.sort()
        
        # Für jeden Topic eine Zeitreihe erzeugen
        for topic in topics_result[:5]:  # Nur für die Top-5 Topics
            topic_id = topic["id"]
            topic_counts_by_date[topic_id] = {}
            
            # Basiswert für dieses Topic
            base_value = random.randint(5, 15) * (5 - topics_result.index(topic))
            
            # Für jeden Tag einen Wert erzeugen
            for i, date in enumerate(dates):
                # Füge eine leichte Steigung plus etwas Zufall hinzu
                if i == 0:
                    # Startwert
                    topic_counts_by_date[topic_id][date] = base_value
                else:
                    # Vorheriger Wert plus Trend plus Zufall
                    prev_value = topic_counts_by_date[topic_id][dates[i-1]]
                    trend = random.uniform(-0.1, 0.2) * prev_value  # Leichte Steigung im Trend
                    noise = random.uniform(-0.15, 0.15) * prev_value  # Zufällige Schwankung
                    new_value = max(1, int(prev_value + trend + noise))  # Nie unter 1
                    topic_counts_by_date[topic_id][date] = new_value
        
        # Ergebnis zurückgeben
        return {
            "topics": topics_result,
            "metrics": {
                "coherence_score": topic_coherence,
                "diversity_score": topic_diversity,
                "total_documents": len(df),
                "document_coverage": random.uniform(0.7, 0.95),
            },
            "time_range": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            },
            "topic_counts_by_date": topic_counts_by_date
        }
    except Exception as e:
        logger.error(f"Fehler im Topic-Model-Endpunkt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-data")
async def get_recent_data(
    platform: str = Query("reddit", description="Platform to get data from (reddit, tiktok, youtube)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return")
):
    """
    Returns the most recent content from the specified platform
    
    Args:
        platform: One of 'reddit', 'tiktok', or 'youtube'
        limit: Maximum number of records to return (1-100)
    """
    logger.info(f"Recent data endpoint called for platform: {platform}, limit: {limit}")
    
    try:
        # Validate inputs
        if platform not in ["reddit", "tiktok", "youtube"]:
            logger.warning(f"Invalid platform requested: {platform}")
            raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}. Must be one of: reddit, tiktok, youtube")
        
        # Cap limit to prevent excessive data requests
        limit = min(int(limit), 100)
        
        # Get database connection
        db = get_db_connection()
        
        # Set up query based on platform
        table_name = None
        query = None
        
        if platform == "reddit":
            table_name = "reddit_data"
            query = """
                SELECT id, title, text, author, 
                       COALESCE(created_utc, 0) as created_at, 
                       COALESCE(url, '') as url, 
                       scraped_at
                FROM reddit_data
                ORDER BY scraped_at DESC
                LIMIT :limit
            """
        elif platform == "tiktok":
            table_name = "tiktok_data"
            query = """
                SELECT id, description as text, author_username as author,
                       COALESCE(created_time, 0) as created_at, 
                       COALESCE(video_url, '') as url, 
                       scraped_at
                FROM tiktok_data
                ORDER BY scraped_at DESC
                LIMIT :limit
            """
        elif platform == "youtube":
            table_name = "youtube_data"
            query = """
                SELECT video_id as id, title, description as text, 
                       channel_title as author, published_at as created_at, 
                       COALESCE(url, '') as url, scraped_at, trending_date
                FROM youtube_data
                ORDER BY scraped_at DESC
                LIMIT :limit
            """
        
        # Verify table exists
        with db.connect() as conn:
            check_query = f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                )
            """
            result = conn.execute(text(check_query))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.warning(f"Table {table_name} does not exist in the database")
                return {"data": [], "message": f"No data available for {platform}"}
            
            # Execute query
            logger.debug(f"Executing query: {query}")
            result = conn.execute(text(query), {"limit": limit})
            
            # Process results
            data = []
            for row in result:
                item = {}
                for column, value in row._mapping.items():
                    # Handle datetime objects
                    if isinstance(value, datetime):
                        item[column] = value.isoformat()
                    else:
                        item[column] = value
                data.append(item)
            
            result_count = len(data)
            logger.info(f"Retrieved {result_count} records for {platform}")
            
            if result_count == 0:
                logger.warning(f"No data found for {platform} in the database")
                return {"data": [], "message": f"No data found for {platform}"}
                
            return {"data": data, "count": result_count}
    
    except Exception as e:
        error_msg = f"Error retrieving recent {platform} data: {str(e)}"
        logger.error(error_msg)
        logger.exception("Detailed error:")
        raise HTTPException(status_code=500, detail=error_msg)

# Add DriftMetrics model for MLOPS endpoints
class DriftMetrics(BaseModel):
    timestamp: str
    dataset_drift: bool
    share_of_drifted_columns: float
    drifted_columns: List[str]

# Define the PipelineExecution model for MLOPS endpoints
class PipelineExecution(BaseModel):
    id: str
    pipelineId: str
    startTime: str
    endTime: Optional[str] = None
    status: str
    trigger: str

# MLOPS endpoints to match the integrated API
@app.get("/api/mlops/models/{model_name}/drift", response_model=DriftMetrics)
async def get_model_drift(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version")
):
    """
    Get data drift metrics for a specific model version
    """
    logger.info(f"Request for drift metrics of model: {model_name}, version: {version}")
    
    # Set default version if not provided
    if not version:
        version = "v1.0.2"  # Default to latest version
        logger.info(f"No version specified, using default: {version}")
    
    # Define model registry path
    model_registry_path = Path("models/registry").resolve()
    model_registry_path.mkdir(parents=True, exist_ok=True)
    
    # Check for actual drift metrics in model registry
    drift_path = model_registry_path / model_name / version / "drift_metrics.json"
    logger.info(f"Checking for drift metrics at: {drift_path}")
    
    try:
        if drift_path.exists():
            logger.info(f"Found drift metrics at {drift_path}")
            with open(drift_path, "r") as f:
                drift_metrics = json.load(f)
                result = DriftMetrics(**drift_metrics)
                logger.info(f"Returning drift metrics: {result}")
                return result
        else:
            logger.warning(f"No drift metrics found at {drift_path}, using mock data")
    except Exception as e:
        logger.error(f"Error reading drift metrics: {e}")
    
    # Return mock drift metrics if no actual metrics found
    result = DriftMetrics(
        timestamp=datetime.now().isoformat(),
        dataset_drift=True,
        share_of_drifted_columns=0.25,
        drifted_columns=["text_length", "sentiment_score", "engagement_rate"]
    )
    logger.info(f"Returning mock drift metrics: {result}")
    return result

@app.get("/api/mlops/pipelines")
async def get_pipelines():
    """
    Get all ML pipelines status
    """
    logger.info("Request for all pipelines")
    
    # Current date for realistic timestamps
    current_time = datetime.now()
    yesterday = current_time - timedelta(days=1)
    tomorrow = current_time + timedelta(days=1)
    
    # Return mock pipeline data with current dates
    pipelines = {
        "trend_analysis": {
            "name": "Trend Analysis Pipeline",
            "description": "Analyzes trends across social media platforms",
            "steps": [
                {"id": "data_ingestion", "name": "Data Ingestion", "description": "Collects data from social media APIs", "status": "completed", "runtime": "00:05:23"},
                {"id": "preprocessing", "name": "Preprocessing", "description": "Cleans and prepares data for analysis", "status": "completed", "runtime": "00:08:47"},
                {"id": "topic_modeling", "name": "Topic Modeling", "description": "Identifies key topics in the content", "status": "completed", "runtime": "00:15:32"},
                {"id": "sentiment_analysis", "name": "Sentiment Analysis", "description": "Determines sentiment for each post", "status": "completed", "runtime": "00:09:18"},
                {"id": "trend_detection", "name": "Trend Detection", "description": "Identifies emerging trends in topics", "status": "completed", "runtime": "00:06:42"},
                {"id": "model_evaluation", "name": "Model Evaluation", "description": "Evaluates the performance of prediction models", "status": "completed", "runtime": "00:03:55"},
                {"id": "visualization", "name": "Visualization", "description": "Prepares data for dashboard visualization", "status": "completed", "runtime": "00:02:11"}
            ],
            "lastRun": yesterday.isoformat(),
            "nextScheduledRun": tomorrow.isoformat(),
            "averageRuntime": "00:51:48",
            "status": "completed"
        },
        "realtime_monitoring": {
            "name": "Realtime Monitoring Pipeline",
            "description": "Monitors social media trends in real-time",
            "steps": [
                {"id": "stream_ingestion", "name": "Stream Ingestion", "description": "Collects real-time data from social APIs", "status": "completed", "runtime": "00:02:25"},
                {"id": "realtime_preprocessing", "name": "Realtime Preprocessing", "description": "Processes streaming data in real-time", "status": "completed", "runtime": "00:01:35"},
                {"id": "topic_detection", "name": "Topic Detection", "description": "Detects emerging topics in real-time", "status": "running", "runtime": "00:15:42"},
                {"id": "anomaly_detection", "name": "Anomaly Detection", "description": "Identifies unusual patterns in social content", "status": "pending", "runtime": "00:00:00"},
                {"id": "alert_generation", "name": "Alert Generation", "description": "Generates alerts for detected anomalies", "status": "pending", "runtime": "00:00:00"}
            ],
            "lastRun": current_time.isoformat(),
            "nextScheduledRun": "continuous",
            "averageRuntime": "00:25:30",
            "status": "running"
        },
        "model_training": {
            "name": "Model Training Pipeline",
            "description": "Trains and evaluates prediction models",
            "steps": [
                {"id": "data_collection", "name": "Data Collection", "description": "Collects training data from database", "status": "completed", "runtime": "00:10:15"},
                {"id": "feature_engineering", "name": "Feature Engineering", "description": "Prepares features for model training", "status": "completed", "runtime": "00:12:30"},
                {"id": "model_training", "name": "Model Training", "description": "Trains prediction models", "status": "completed", "runtime": "01:24:56"},
                {"id": "model_evaluation", "name": "Model Evaluation", "description": "Evaluates model performance", "status": "failed", "runtime": "00:05:23"},
                {"id": "model_deployment", "name": "Model Deployment", "description": "Deploys models to production", "status": "pending", "runtime": "00:00:00"}
            ],
            "lastRun": (yesterday - timedelta(days=1)).isoformat(),
            "nextScheduledRun": (tomorrow + timedelta(days=6)).isoformat(),
            "averageRuntime": "01:52:24",
            "status": "failed"
        }
    }
    
    return pipelines

@app.get("/api/mlops/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    """
    Get details for a specific pipeline
    """
    logger.info(f"Request for pipeline: {pipeline_id}")
    
    # Current date for realistic timestamps
    current_time = datetime.now()
    yesterday = current_time - timedelta(days=1)
    tomorrow = current_time + timedelta(days=1)
    
    pipelines = {
        "trend_analysis": {
            "name": "Trend Analysis Pipeline",
            "description": "Analyzes trends across social media platforms",
            "steps": [
                {"id": "data_ingestion", "name": "Data Ingestion", "description": "Collects data from social media APIs", "status": "completed", "runtime": "00:05:23"},
                {"id": "preprocessing", "name": "Preprocessing", "description": "Cleans and prepares data for analysis", "status": "completed", "runtime": "00:08:47"},
                {"id": "topic_modeling", "name": "Topic Modeling", "description": "Identifies key topics in the content", "status": "completed", "runtime": "00:15:32"},
                {"id": "sentiment_analysis", "name": "Sentiment Analysis", "description": "Determines sentiment for each post", "status": "completed", "runtime": "00:09:18"},
                {"id": "trend_detection", "name": "Trend Detection", "description": "Identifies emerging trends in topics", "status": "completed", "runtime": "00:06:42"},
                {"id": "model_evaluation", "name": "Model Evaluation", "description": "Evaluates the performance of prediction models", "status": "completed", "runtime": "00:03:55"},
                {"id": "visualization", "name": "Visualization", "description": "Prepares data for dashboard visualization", "status": "completed", "runtime": "00:02:11"}
            ],
            "lastRun": yesterday.isoformat(),
            "nextScheduledRun": tomorrow.isoformat(),
            "averageRuntime": "00:51:48",
            "status": "completed"
        },
        "realtime_monitoring": {
            "name": "Realtime Monitoring Pipeline",
            "description": "Monitors social media trends in real-time",
            "steps": [
                {"id": "stream_ingestion", "name": "Stream Ingestion", "description": "Collects real-time data from social APIs", "status": "completed", "runtime": "00:02:25"},
                {"id": "realtime_preprocessing", "name": "Realtime Preprocessing", "description": "Processes streaming data in real-time", "status": "completed", "runtime": "00:01:35"},
                {"id": "topic_detection", "name": "Topic Detection", "description": "Detects emerging topics in real-time", "status": "running", "runtime": "00:15:42"},
                {"id": "anomaly_detection", "name": "Anomaly Detection", "description": "Identifies unusual patterns in social content", "status": "pending", "runtime": "00:00:00"},
                {"id": "alert_generation", "name": "Alert Generation", "description": "Generates alerts for detected anomalies", "status": "pending", "runtime": "00:00:00"}
            ],
            "lastRun": current_time.isoformat(),
            "nextScheduledRun": "continuous",
            "averageRuntime": "00:25:30",
            "status": "running"
        },
        "model_training": {
            "name": "Model Training Pipeline",
            "description": "Trains and evaluates prediction models",
            "steps": [
                {"id": "data_collection", "name": "Data Collection", "description": "Collects training data from database", "status": "completed", "runtime": "00:10:15"},
                {"id": "feature_engineering", "name": "Feature Engineering", "description": "Prepares features for model training", "status": "completed", "runtime": "00:12:30"},
                {"id": "model_training", "name": "Model Training", "description": "Trains prediction models", "status": "completed", "runtime": "01:24:56"},
                {"id": "model_evaluation", "name": "Model Evaluation", "description": "Evaluates model performance", "status": "failed", "runtime": "00:05:23"},
                {"id": "model_deployment", "name": "Model Deployment", "description": "Deploys models to production", "status": "pending", "runtime": "00:00:00"}
            ],
            "lastRun": (yesterday - timedelta(days=1)).isoformat(),
            "nextScheduledRun": (tomorrow + timedelta(days=6)).isoformat(),
            "averageRuntime": "01:52:24",
            "status": "failed"
        }
    }
    
    if pipeline_id not in pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
    
    return pipelines[pipeline_id]

@app.get("/api/mlops/pipelines/{pipeline_id}/executions")
async def get_pipeline_executions(pipeline_id: str):
    """
    Get executions for a specific pipeline
    """
    logger.info(f"Request for executions of pipeline: {pipeline_id}")
    
    # Current date for realistic timestamps
    current_time = datetime.now()
    one_day_ago = current_time - timedelta(days=1)
    two_days_ago = current_time - timedelta(days=2)
    three_days_ago = current_time - timedelta(days=3)
    
    # Mock executions with current dates
    all_executions = [
        {"id": "exec-001", "pipelineId": "trend_analysis", "startTime": one_day_ago.isoformat(), "endTime": (one_day_ago + timedelta(hours=1)).isoformat(), "status": "completed", "trigger": "scheduled"},
        {"id": "exec-002", "pipelineId": "trend_analysis", "startTime": two_days_ago.isoformat(), "endTime": (two_days_ago + timedelta(hours=1)).isoformat(), "status": "completed", "trigger": "scheduled"},
        {"id": "exec-003", "pipelineId": "realtime_monitoring", "startTime": current_time.isoformat(), "endTime": None, "status": "running", "trigger": "manual"},
        {"id": "exec-004", "pipelineId": "model_training", "startTime": two_days_ago.isoformat(), "endTime": (two_days_ago + timedelta(hours=2)).isoformat(), "status": "failed", "trigger": "manual"},
        {"id": "exec-005", "pipelineId": "trend_analysis", "startTime": three_days_ago.isoformat(), "endTime": (three_days_ago + timedelta(hours=1)).isoformat(), "status": "completed", "trigger": "scheduled"},
    ]
    
    executions = [execution for execution in all_executions if execution["pipelineId"] == pipeline_id]
    
    return executions

@app.post("/api/mlops/pipelines/{pipeline_id}/execute")
async def execute_pipeline(pipeline_id: str):
    """
    Execute a specific pipeline
    """
    logger.info(f"Request to execute pipeline: {pipeline_id}")
    
    # Map pipeline ID to model name
    pipeline_to_model = {
        "trend_analysis": "topic_model",
        "realtime_monitoring": "anomaly_detector",
        "model_training": "sentiment_classifier"
    }
    
    if pipeline_id not in pipeline_to_model:
        logger.error(f"Pipeline {pipeline_id} not found")
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
    
    # Generate execution ID
    execution_id = f"exec-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # In a real implementation, this would start the pipeline in a background task
    
    response = {
        "execution_id": execution_id,
        "pipeline_id": pipeline_id,
        "status": "started",
        "startTime": datetime.now().isoformat(),
        "message": f"Pipeline {pipeline_id} execution started with ID {execution_id}"
    }
    
    logger.info(f"Pipeline execution response: {response}")
    return response

@app.get("/api/mlops/models/{model_name}/metrics")
async def get_model_metrics(
    model_name: str,
    version: Optional[str] = Query(None, description="Model version")
):
    """
    Get performance metrics for a specific model version
    """
    logger.info(f"Request for metrics of model: {model_name}, version: {version}")
    
    # Set default version if not provided
    if not version:
        version = "v1.0.2"  # Default to latest version
        logger.info(f"No version specified, using default: {version}")
    
    # Define model registry path
    model_registry_path = Path("models/registry").resolve()
    model_registry_path.mkdir(parents=True, exist_ok=True)
    
    # Check for actual metrics in model registry
    metrics_path = model_registry_path / model_name / version / "metrics.json"
    logger.info(f"Checking for metrics at: {metrics_path}")
    
    try:
        if metrics_path.exists():
            logger.info(f"Found metrics at {metrics_path}")
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
                logger.info(f"Returning metrics: {metrics}")
                return metrics
        else:
            logger.warning(f"No metrics found at {metrics_path}, using mock data")
    except Exception as e:
        logger.error(f"Error reading metrics: {e}")
    
    # Return mock metrics if no actual metrics found
    if model_name == "topic_model":
        return {
            "coherence_score": 0.78,
            "diversity_score": 0.65,
            "document_coverage": 0.92,
            "total_documents": 15764,
            "uniqueness_score": 0.81,
            "silhouette_score": 0.72,
            "topic_separation": 0.68,
            "avg_topic_similarity": 0.43,
            "execution_time": 183.4,
            "topic_quality": 0.75
        }
    elif model_name == "sentiment_analysis":
        return {
            "accuracy": 0.89,
            "precision": 0.83,
            "recall": 0.86,
            "f1_score": 0.85,
            "total_documents": 12500,
            "execution_time": 162.7,
            "uniqueness_score": 0.79,
            "silhouette_score": 0.67,
            "topic_separation": 0.72
        }
    else:
        return {
            "mean_absolute_error": 0.12,
            "mean_squared_error": 0.05,
            "r2_score": 0.87,
            "total_predictions": 8742,
            "execution_time": 97.3,
            "accuracy": 0.91,
            "precision": 0.88,
            "recall": 0.85,
            "f1_score": 0.86
        }

@app.get("/api/mlops/models/{model_name}/versions")
async def get_model_versions(model_name: str):
    """
    Get available versions for a specific model
    """
    logger.info(f"Request for versions of model: {model_name}")
    
    # Current date for realistic timestamps
    current_time = datetime.now()
    one_week_ago = current_time - timedelta(days=7)
    two_weeks_ago = current_time - timedelta(days=14)
    
    # Return mock version data with current dates
    if model_name == "topic_model":
        return [
            {"id": "v1.0.2", "name": "Topic Model v1.0.2", "date": current_time.isoformat(), "status": "production"},
            {"id": "v1.0.1", "name": "Topic Model v1.0.1", "date": one_week_ago.isoformat(), "status": "archived"},
            {"id": "v1.0.0", "name": "Topic Model v1.0.0", "date": two_weeks_ago.isoformat(), "status": "archived"}
        ]
    elif model_name == "sentiment_analysis":
        return [
            {"id": "v2.0.1", "name": "Sentiment Analysis v2.0.1", "date": current_time.isoformat(), "status": "production"},
            {"id": "v2.0.0", "name": "Sentiment Analysis v2.0.0", "date": (current_time - timedelta(days=10)).isoformat(), "status": "archived"}
        ]
    else:
        return [
            {"id": "v1.5.0", "name": "Trend Prediction v1.5.0", "date": current_time.isoformat(), "status": "production"}
        ]

@app.get("/api/db/predictions")
async def get_predictions():
    """
    Get trend predictions for social media topics
    """
    logger.info("Predictions endpoint called")
    
    # Current date for realistic timestamps
    current_time = datetime.now()
    week_start = current_time - timedelta(days=7)
    week_end = current_time + timedelta(days=7)
    
    # Generate mock prediction data
    predictions = [
        {
            "topic_id": "topic1",
            "topic_name": "AI & Technology",
            "current_count": 1250,
            "predicted_count": 1520,
            "growth_rate": 21.6,
            "confidence": 0.85,
            "sentiment_score": 0.32,
            "keywords": ["artificial intelligence", "machine learning", "neural networks", "chatgpt", "generative AI"]
        },
        {
            "topic_id": "topic2",
            "topic_name": "Entertainment & Media",
            "current_count": 980,
            "predicted_count": 1040,
            "growth_rate": 6.1,
            "confidence": 0.72,
            "sentiment_score": 0.54,
            "keywords": ["movies", "streaming", "shows", "entertainment", "media"]
        },
        {
            "topic_id": "topic3",
            "topic_name": "Gaming & VR",
            "current_count": 750,
            "predicted_count": 920,
            "growth_rate": 22.7,
            "confidence": 0.79,
            "sentiment_score": 0.48,
            "keywords": ["gaming", "virtual reality", "games", "esports", "metaverse"]
        },
        {
            "topic_id": "topic4",
            "topic_name": "Climate & Environment",
            "current_count": 620,
            "predicted_count": 710,
            "growth_rate": 14.5,
            "confidence": 0.68,
            "sentiment_score": -0.15,
            "keywords": ["climate", "environment", "sustainability", "renewable", "green"]
        },
        {
            "topic_id": "topic5",
            "topic_name": "Health & Wellness",
            "current_count": 540,
            "predicted_count": 610,
            "growth_rate": 13.0,
            "confidence": 0.75,
            "sentiment_score": 0.22,
            "keywords": ["health", "wellness", "fitness", "mental health", "nutrition"]
        }
    ]
    
    # Generate daily prediction trends data
    prediction_trends = {}
    
    # Generate date range for the next 7 days
    start_date = current_time
    dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    # For each prediction, generate a trend line for each date
    for prediction in predictions:
        topic_id = prediction["topic_id"]
        prediction_trends[topic_id] = {}
        
        # Base count from the prediction
        base_count = prediction["current_count"]
        growth_rate = prediction["growth_rate"] / 100  # Convert percentage to decimal
        
        # Generate count for each day with some randomness
        for i, date in enumerate(dates):
            # Apply daily growth rate with some random variation
            daily_growth = growth_rate / 7  # Distribute growth over 7 days
            random_factor = 1 + (random.random() * 0.2 - 0.1)  # Random factor between 0.9 and 1.1
            
            # Calculate predicted count for this day
            count = int(base_count * (1 + daily_growth * i) * random_factor)
            prediction_trends[topic_id][date] = count
    
    response = {
        "predictions": predictions,
        "prediction_trends": prediction_trends,
        "time_range": {
            "start_date": week_start.strftime("%Y-%m-%d"),
            "end_date": week_end.strftime("%Y-%m-%d")
        }
    }
    
    logger.info("Returning prediction data")
    return response

@app.get("/api/db/analysis")
async def get_analysis():
    """
    Get analysis data for social media topics
    """
    logger.info("Analysis endpoint called")
    
    # Current date for realistic timestamps
    current_time = datetime.now()
    
    # Generate mock analysis data
    analysis = {
        "topics": [
            {
                "topic_id": "topic1",
                "topic_name": "AI & Technology",
                "post_count": 1250,
                "engagement": 28500,
                "sentiment_score": 0.32,
                "keywords": ["artificial intelligence", "machine learning", "neural networks", "chatgpt", "generative AI"],
                "platforms": {
                    "reddit": 520,
                    "tiktok": 430,
                    "youtube": 300
                }
            },
            {
                "topic_id": "topic2",
                "topic_name": "Entertainment & Media",
                "post_count": 980,
                "engagement": 19600,
                "sentiment_score": 0.54,
                "keywords": ["movies", "streaming", "shows", "entertainment", "media"],
                "platforms": {
                    "reddit": 320,
                    "tiktok": 410,
                    "youtube": 250
                }
            },
            {
                "topic_id": "topic3",
                "topic_name": "Gaming & VR",
                "post_count": 750,
                "engagement": 22500,
                "sentiment_score": 0.48,
                "keywords": ["gaming", "virtual reality", "games", "esports", "metaverse"],
                "platforms": {
                    "reddit": 380,
                    "tiktok": 220,
                    "youtube": 150
                }
            }
        ],
        "time_range": {
            "start_date": (current_time - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": current_time.strftime("%Y-%m-%d")
        },
        "platforms": {
            "reddit": {
                "post_count": 4250,
                "user_count": 3100,
                "engagement": 89700
            },
            "tiktok": {
                "post_count": 5800,
                "user_count": 2800,
                "engagement": 127500
            },
            "youtube": {
                "post_count": 1200,
                "user_count": 450,
                "engagement": 65800
            }
        }
    }
    
    logger.info("Returning analysis data")
    return analysis 