import os
import praw
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import psycopg2
from psycopg2.extras import execute_values

# Load environment variables
load_dotenv()

# Setup paths and logging
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure logger with file and console handlers
logger = logging.getLogger("reddit_scraper")
logger.setLevel(logging.INFO)

# File handler with rotation
log_handler = RotatingFileHandler(
    LOG_DIR / "reddit.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=5
)
log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(log_handler)

# Console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

def get_db_connection():
    """Create a connection to the database specified in DATABASE_URL"""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    try:
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def remove_duplicates(posts):
    """
    Remove duplicate posts based on title, text, and subreddit
    
    Args:
        posts: List of post dictionaries
        
    Returns:
        List of unique posts
    """
    seen = set()
    unique_posts = []
    
    for post in posts:
        key = (post["title"], post["text"], post["subreddit"])
        if key not in seen:
            seen.add(key)
            unique_posts.append(post)
    
    return unique_posts

def scrape_reddit():
    """
    Scrape trending posts from Reddit and store in the database
    
    Fetches hot posts from specified subreddits, processes them,
    and saves to the PostgreSQL database with duplicate handling.
    """
    try:
        logger.info("Starting Reddit scraping...")

        # Check for Reddit API credentials
        reddit_id = os.getenv("REDDIT_ID")
        reddit_secret = os.getenv("REDDIT_SECRET")
        
        if not reddit_id or not reddit_secret:
            logger.error("Reddit API credentials missing. Check your .env file.")
            return
            
        # Remove any quotes and whitespace from credentials
        reddit_id = reddit_id.strip().strip('"\'')
        reddit_secret = reddit_secret.strip().strip('"\'')
     
        # Setup Reddit API connection
        user_agent = "python:TrendAnalysis:v1.0 (by u/YourRedditUsername)"
        
        try:
            reddit = praw.Reddit(
                client_id=reddit_id,
                client_secret=reddit_secret,
                user_agent=user_agent
            )
            
        except Exception as e:
            logger.error(f"Failed to connect to Reddit API: {str(e)}")
            # Create status entry on error
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO public.reddit_data 
                        (id, title, text, author, score, created_utc, num_comments, url, subreddit, scraped_at)
                        VALUES ('status_update', 'Reddit API Error', %s, 'Scraper', 0, 0, 0, 
                                'https://example.com', 'status', %s)
                        ON CONFLICT (id) DO UPDATE SET 
                            text = EXCLUDED.text,
                            scraped_at = EXCLUDED.scraped_at
                    """, (str(e), datetime.now()))
                    conn.commit()
            return

        # Configure scraping parameters
        subreddits = ["all", "popular", "trendingreddits", "trendingsubreddits"]
        post_limit = 100
        all_posts = []
        scrape_time = datetime.now()

        # Fetch posts from each subreddit
        for sub in subreddits:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.hot(limit=post_limit):
                if post.is_self:  # Only collect text posts
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

        # Remove duplicates from the current batch
        unique_posts = remove_duplicates(all_posts)
        logger.info(f"Found {len(unique_posts)} unique posts out of {len(all_posts)} total posts")
        
        # Store data in PostgreSQL
        if unique_posts:
            with get_db_connection() as conn:
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
                    
                    # Get count before insertion
                    cur.execute("SELECT COUNT(*) FROM reddit_data")
                    count_before = cur.fetchone()[0]
                    
                    inserted = 0
                    updated = 0
                    
                    # Process each post with conflict handling
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
                            
                            # Check if it was an insert or update
                            result = cur.fetchone()
                            if result[0]:
                                inserted += 1
                            else:
                                updated += 1
                                
                        except Exception as e:
                            logger.error(f"Error inserting post {post['id']}: {str(e)}")
                            continue
                    
                    # Commit changes and log results
                    conn.commit()
                    
                    # Calculate totals
                    logger.info(f"Successfully processed Reddit posts: {inserted} new, {updated} updated")
                    logger.info(f"Total posts in database: {count_before + inserted}")

    except Exception as e:
        logger.error(f"Error in Reddit scraper: {str(e)}")
        logger.exception("Detailed error:")
        
        # Update status record to show error
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO public.reddit_data 
                        (id, title, text, author, score, created_utc, num_comments, url, subreddit, scraped_at)
                        VALUES ('status_update', 'Reddit Scraper Error', %s, 'Scraper', 0, 0, 0, 
                                'https://example.com', 'status', %s)
                        ON CONFLICT (id) DO UPDATE SET 
                            text = EXCLUDED.text,
                            scraped_at = EXCLUDED.scraped_at
                    """, (str(e), datetime.now()))
                    conn.commit()
        except Exception as status_error:
            logger.error(f"Error updating status: {str(status_error)}")

if __name__ == "__main__":
    scrape_reddit()