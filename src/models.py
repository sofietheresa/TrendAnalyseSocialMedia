from sqlalchemy import Column, Integer, String, DateTime, BigInteger, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Basis-Klasse für SQLAlchemy-Modelle
Base = declarative_base()

class RedditData(Base):
    __tablename__ = 'reddit_data'

    id = Column(String, primary_key=True)
    title = Column(String)
    text = Column(String)
    author = Column(String)
    score = Column(Integer)
    created_utc = Column(BigInteger)
    num_comments = Column(Integer)
    url = Column(String)
    subreddit = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow)

class TikTokData(Base):
    __tablename__ = 'tiktok_data'

    id = Column(String, primary_key=True)
    description = Column(String)
    author_username = Column(String)
    author_id = Column(String)
    likes = Column(Integer)
    shares = Column(Integer)
    comments = Column(Integer)
    plays = Column(Integer)
    video_url = Column(String)
    created_time = Column(BigInteger)
    scraped_at = Column(DateTime, default=datetime.utcnow)

class YouTubeData(Base):
    __tablename__ = 'youtube_data'

    video_id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(String)
    channel_title = Column(String)
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)
    published_at = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)

# Datenbankverbindung
def get_db_url():
    """Gibt die Datenbank-URL basierend auf den Umgebungsvariablen zurück"""
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "social_media")
    
    return f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Engine und Session erstellen
engine = create_engine(get_db_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialisiert die Datenbank und erstellt alle Tabellen"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency für FastAPI, die eine Datenbankverbindung bereitstellt"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 