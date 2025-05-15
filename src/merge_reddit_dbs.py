import os
import psycopg2
from urllib.parse import urlparse
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def merge_tables():
    try:
        # Connect to the railway database
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Get data from reddit_posts
        cur.execute("SELECT * FROM reddit_posts")
        rows = cur.fetchall()
        logger.info(f"Found {len(rows)} rows in reddit_posts table")
        
        # Get column names and their order from reddit_posts
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'reddit_posts' 
            ORDER BY ordinal_position
        """)
        source_columns = [col[0] for col in cur.fetchall()]
        
        # Get column names from reddit_data
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'reddit_data' 
            ORDER BY ordinal_position
        """)
        target_columns = [col[0] for col in cur.fetchall()]
        
        # Map columns from reddit_posts to reddit_data
        column_mapping = {
            'id': 'id',
            'subreddit': 'subreddit',
            'title': 'title',
            'text': 'text',
            'score': 'score',
            'comments': 'num_comments',
            'created': 'created_utc',
            'url': 'url',
            'scraped_at': 'scraped_at'
        }
        
        inserted = 0
        updated = 0
        
        for row in rows:
            # Create a dictionary of the current row
            row_dict = dict(zip(source_columns, row))
            
            # Convert timestamp to Unix timestamp for created_utc
            created_ts = int(row_dict['created'].timestamp()) if row_dict['created'] else None
            
            try:
                # Try to insert with ON CONFLICT DO UPDATE
                cur.execute("""
                    INSERT INTO reddit_data (
                        id, title, text, score, created_utc, num_comments, 
                        url, subreddit, scraped_at, author
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (id) 
                    DO UPDATE SET
                        score = EXCLUDED.score,
                        num_comments = EXCLUDED.num_comments,
                        scraped_at = EXCLUDED.scraped_at
                    RETURNING (xmax = 0) AS inserted
                """, (
                    str(row_dict['id']),  # Convert to string as reddit_data.id is varchar
                    row_dict['title'],
                    row_dict['text'],
                    row_dict['score'],
                    created_ts,
                    row_dict['comments'],
                    row_dict['url'],
                    row_dict['subreddit'],
                    row_dict['scraped_at'],
                    None  # author field doesn't exist in reddit_posts
                ))
                
                # Check if it was an insert or update
                result = cur.fetchone()
                if result[0]:
                    inserted += 1
                else:
                    updated += 0
                    
            except Exception as e:
                logger.error(f"Error processing row {row_dict['id']}: {e}")
                continue
        
        logger.info(f"Successfully migrated data: {inserted} rows inserted, {updated} rows updated")
        
        # Drop the reddit_posts table
        cur.execute("DROP TABLE reddit_posts")
        logger.info("Successfully dropped reddit_posts table")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise

if __name__ == "__main__":
    merge_tables() 