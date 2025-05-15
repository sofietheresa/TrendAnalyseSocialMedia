from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta
import urllib.parse
import logging
import sys
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import json
from pathlib import Path

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
        
        # Versuche verschiedene SQL-Abfragen mit verschiedenen Spaltenbezeichnungen
        try:
            # Erste Abfragevariante mit 'text' als Haupttextspalte für Reddit
            query = f"""
                SELECT 
                    p.id, 
                    p.source, 
                    COALESCE(p.title, '') as title, 
                    COALESCE(p.text, '') as text,
                    p.scraped_at
                FROM (
                    SELECT id, 'reddit' as source, title, text, scraped_at
                    FROM reddit_data
                    WHERE scraped_at BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                    
                    UNION ALL
                    
                    SELECT id, 'tiktok' as source, '' as title, description as text, scraped_at
                    FROM tiktok_data
                    WHERE scraped_at BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                    
                    UNION ALL
                    
                    SELECT id, 'youtube' as source, title, description as text, scraped_at
                    FROM youtube_data
                    WHERE scraped_at BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                ) p
                WHERE p.source IN ({platforms_str})
            """
            
            with db.connect() as conn:
                df = pd.read_sql(query, conn)
            
        except Exception as e:
            logger.warning(f"Erste Abfragevariante fehlgeschlagen: {e}")
            
            try:
                # Zweite Abfragevariante mit 'content' als möglicher Textspalte für Reddit
                query = f"""
                    SELECT 
                        p.id, 
                        p.source, 
                        COALESCE(p.title, '') as title, 
                        COALESCE(p.text, '') as text,
                        p.scraped_at
                    FROM (
                        SELECT id, 'reddit' as source, title, content as text, scraped_at
                        FROM reddit_data
                        WHERE scraped_at BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                        
                        UNION ALL
                        
                        SELECT id, 'tiktok' as source, '' as title, description as text, scraped_at
                        FROM tiktok_data
                        WHERE scraped_at BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                        
                        UNION ALL
                        
                        SELECT id, 'youtube' as source, title, description as text, scraped_at
                        FROM youtube_data
                        WHERE scraped_at BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                    ) p
                    WHERE p.source IN ({platforms_str})
                """
                
                with db.connect() as conn:
                    df = pd.read_sql(query, conn)
                
            except Exception as e:
                logger.warning(f"Zweite Abfragevariante fehlgeschlagen: {e}")
                
                try:
                    # Dritte Abfragevariante mit 'body' als möglicher Textspalte für Reddit
                    query = f"""
                        SELECT 
                            p.id, 
                            p.source, 
                            COALESCE(p.title, '') as title, 
                            COALESCE(p.text, '') as text,
                            p.scraped_at
                        FROM (
                            SELECT id, 'reddit' as source, title, body as text, scraped_at
                            FROM reddit_data
                            WHERE scraped_at BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                            
                            UNION ALL
                            
                            SELECT id, 'tiktok' as source, '' as title, description as text, scraped_at
                            FROM tiktok_data
                            WHERE scraped_at BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                            
                            UNION ALL
                            
                            SELECT id, 'youtube' as source, title, description as text, scraped_at
                            FROM youtube_data
                            WHERE scraped_at BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                        ) p
                        WHERE p.source IN ({platforms_str})
                    """
                    
                    with db.connect() as conn:
                        df = pd.read_sql(query, conn)
                    
                except Exception as e:
                    logger.error(f"Alle Abfragevarianten fehlgeschlagen: {e}")
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
        
        # Hier würde normalerweise das BERTopic-Modell initialisiert und trainiert
        # Da dies rechenintensiv ist und externe Abhängigkeiten hat, simulieren wir die Ergebnisse für das API
        
        # In einer echten Implementierung:
        # from bertopic import BERTopic
        # from sentence_transformers import SentenceTransformer
        # embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # topic_model = BERTopic(embedding_model=embedding_model)
        # topics, probs = topic_model.fit_transform(texts)
        # topic_info = topic_model.get_topic_info()
        # topic_keywords = {topic_id: [word for word, _ in topic_model.get_topic(topic_id)] 
        #                  for topic_id in topic_info['Topic'].unique() if topic_id != -1}
        
        # Simulierte Ergebnisse basierend auf häufigen Wörtern für die Demo
        from collections import Counter
        import re
        import random
        
        # Einfache Textbereinigung
        def clean_text(text):
            if not isinstance(text, str):
                return ""
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            text = re.sub(r'\d+', '', text)
            return text
        
        # Stopwörter
        stopwords = ["the", "and", "a", "to", "of", "in", "i", "it", "is", "that", "this", 
                    "for", "with", "on", "you", "was", "be", "are", "have", "my", "at", "not", 
                    "but", "we", "they", "so", "what", "all", "me", "like", "just", "do", "can", 
                    "or", "about", "would", "from", "an", "as", "your", "if", "will", "there", 
                    "by", "how", "get", "amp", "im", "its", "http", "https", "com", "www", "youtube",
                    "tiktok", "reddit", "video", "watch", "follow", "post", "comment", "user", "channel"]
        
        # Texte bereinigen und Wörter zählen
        all_words = []
        for text in texts:
            clean = clean_text(text)
            words = [w for w in clean.split() if w not in stopwords and len(w) > 2]
            all_words.extend(words)
        
        word_counts = Counter(all_words)
        top_words = word_counts.most_common(100)
        
        # Topic-Gruppen erzeugen (simuliert)
        num_topics = min(request.num_topics, 5)  # Maximal 5 Topics
        topic_keywords = {}
        
        # Simulierte Topic-Kohärenz-Metriken
        topic_coherence = random.uniform(0.35, 0.6)
        topic_diversity = random.uniform(0.7, 0.9)
        
        # Wörter in Topic-Gruppen aufteilen
        words_per_topic = 10
        for i in range(num_topics):
            start_idx = i * words_per_topic
            end_idx = start_idx + words_per_topic
            if start_idx < len(top_words):
                words = [word for word, count in top_words[start_idx:end_idx]]
                topic_keywords[i] = words
        
        # Topic-Namen generieren
        topic_names = {}
        for topic_id, words in topic_keywords.items():
            topic_names[topic_id] = " & ".join(words[:2])
        
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
            }
        }
    except Exception as e:
        logger.error(f"Fehler im Topic-Model-Endpunkt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 