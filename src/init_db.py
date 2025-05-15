import os
import psycopg2
from urllib.parse import urlparse

def init_databases():
    # Get the base connection URL
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    result = urlparse(url)
    
    # Connect to default database first
    conn = psycopg2.connect(url)
    conn.autocommit = True  # This needs to be set before creating databases
    cur = conn.cursor()
    
    # Create databases if they don't exist
    databases = ["reddit_data", "tiktok_data", "youtube_data"]
    for db in databases:
        try:
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db}'")
            if not cur.fetchone():
                print(f"Creating database: {db}")
                cur.execute(f'CREATE DATABASE {db}')
            else:
                print(f"Database already exists: {db}")
        except Exception as e:
            print(f"Error creating database {db}: {e}")
    
    cur.close()
    conn.close()
    
    # Initialize tables in each database
    for db in databases:
        try:
            db_url = f"{result.scheme}://{result.username}:{result.password}@{result.hostname}:{result.port}/{db}"
            conn = psycopg2.connect(db_url)
            conn.autocommit = True
            cur = conn.cursor()
            
            if db == "reddit_data":
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS reddit_posts (
                        id SERIAL PRIMARY KEY,
                        subreddit TEXT,
                        title TEXT,
                        text TEXT,
                        score INTEGER,
                        comments INTEGER,
                        created TIMESTAMP,
                        url TEXT,
                        scraped_at TIMESTAMP,
                        UNIQUE(title, text, subreddit)
                    )
                """)
            elif db == "tiktok_data":
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tiktok_posts (
                        id SERIAL PRIMARY KEY,
                        video_id TEXT,
                        description TEXT,
                        author_username TEXT,
                        author_id TEXT,
                        likes INTEGER,
                        shares INTEGER,
                        comments INTEGER,
                        plays INTEGER,
                        video_url TEXT,
                        created_time INTEGER,
                        scraped_at TIMESTAMP,
                        UNIQUE(video_id)
                    )
                """)
            elif db == "youtube_data":
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS youtube_videos (
                        id SERIAL PRIMARY KEY,
                        video_id VARCHAR(50),
                        title TEXT,
                        description TEXT,
                        channel_title VARCHAR(255),
                        published_at TIMESTAMP,
                        view_count INTEGER,
                        like_count INTEGER,
                        comment_count INTEGER,
                        url TEXT,
                        scraped_at TIMESTAMP,
                        trending_date DATE,
                        UNIQUE(video_id, trending_date)
                    )
                """)
            print(f"Initialized tables in {db}")
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error initializing tables in {db}: {e}")

if __name__ == "__main__":
    init_databases() 