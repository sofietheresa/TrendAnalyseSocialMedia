import os
import praw
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import psycopg2
from psycopg2.extras import execute_values
import urllib.parse

# Load .env file
load_dotenv()

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging setup with rotation
log_handler = RotatingFileHandler(
    LOG_DIR / "reddit.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=5
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger = logging.getLogger("reddit_scraper")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Also add console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
logger.addHandler(console_handler)

def get_db_connection():
    """
    Create a connection to the main database specified in DATABASE_URL
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        # Connect directly to the main database (railway)
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def remove_duplicates(posts):
    seen = set()
    unique_posts = []
    
    for post in posts:
        key = (post["title"], post["text"], post["subreddit"])
        if key not in seen:
            seen.add(key)
            unique_posts.append(post)
    
    return unique_posts

# scrape Reddit
def scrape_reddit():
    try:
        logger.info("Starting Reddit scraping...")

        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_ID"),
            client_secret=os.getenv("REDDIT_SECRET"),
            user_agent="TrendAnalysis/1.0"
        )
        logger.info("Successfully connected to Reddit API")

        subreddits = ["all", "popular", "trendingreddits", "trendingsubreddits"]
        post_limit = 100
        all_posts = []
        scrape_time = datetime.now()

        for sub in subreddits:
            logger.info(f"Scraping subreddit: r/{sub}")
            subreddit = reddit.subreddit(sub)
            post_count = 0
            for post in subreddit.hot(limit=post_limit):
                if post.is_self:
                    all_posts.append({
                        "id": str(post.id),
                        "subreddit": sub,
                        "title": post.title,
                        "text": post.selftext,
                        "author": str(post.author) if post.author else None,
                        "score": post.score,
                        "created_utc": post.created_utc,
                        "num_comments": post.num_comments,
                        "url": post.url,
                        "scraped_at": scrape_time
                    })
                    post_count += 1
            logger.info(f"Found {post_count} posts in r/{sub}")

        # Remove duplicates from the current batch
        unique_posts = remove_duplicates(all_posts)
        logger.info(f"Found {len(unique_posts)} unique posts out of {len(all_posts)} total posts")
        
        # Store in PostgreSQL
        if unique_posts:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    # Create table if it doesn't exist
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS public.reddit_data (
                            id VARCHAR(50),
                            title TEXT,
                            text TEXT,
                            author VARCHAR(100),
                            score INTEGER,
                            created_utc BIGINT,
                            num_comments INTEGER,
                            url TEXT,
                            subreddit VARCHAR(100),
                            scraped_at TIMESTAMP,
                            PRIMARY KEY (id)
                        )
                    """)
                    conn.commit()
                    
                    inserted = 0
                    updated = 0
                    
                    # Process each post individually
                    for post in unique_posts:
                        try:
                            cur.execute("""
                                INSERT INTO public.reddit_data (
                                    id, title, text, author, score, created_utc,
                                    num_comments, url, subreddit, scraped_at
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (id) 
                                DO UPDATE SET 
                                    score = EXCLUDED.score,
                                    num_comments = EXCLUDED.num_comments,
                                    scraped_at = EXCLUDED.scraped_at
                                RETURNING (xmax = 0) as inserted
                            """, (
                                post["id"],
                                post["title"],
                                post["text"],
                                post["author"],
                                post["score"],
                                post["created_utc"],
                                post["num_comments"],
                                post["url"],
                                post["subreddit"],
                                post["scraped_at"]
                            ))
                            
                            result = cur.fetchone()
                            if result[0]:
                                inserted += 1
                            else:
                                updated += 1
                            
                            conn.commit()
                        except Exception as e:
                            logger.error(f"Error processing post {post['id']}: {str(e)}")
                            conn.rollback()
                            continue

                    logger.info(f"Successfully processed {inserted + updated} Reddit posts ({inserted} inserted, {updated} updated)")

            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                logger.exception("Detailed error:")
            finally:
                conn.close()

    except Exception as e:
        logger.error(f"Error during Reddit scraping: {str(e)}")
        logger.exception("Detailed error:")

if __name__ == "__main__":
    scrape_reddit()