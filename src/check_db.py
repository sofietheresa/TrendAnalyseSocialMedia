import os
import psycopg2
from urllib.parse import urlparse
from datetime import datetime, timedelta
from tabulate import tabulate

def get_db_connection(db_name):
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    result = urlparse(url)
    new_url = f"{result.scheme}://{result.username}:{result.password}@{result.hostname}:{result.port}/{db_name}"
    return psycopg2.connect(new_url)

def check_database(db_name):
    print(f"\nChecking {db_name} database:")
    print("-" * 50)
    
    try:
        conn = get_db_connection(db_name)
        cur = conn.cursor()
        
        # Get table name based on database
        table_name = {
            "reddit_data": "reddit_posts",
            "tiktok_data": "tiktok_posts",
            "youtube_data": "youtube_videos"
        }[db_name]
        
        # Check table structure
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cur.fetchall()
        print("\nTable structure:")
        print(tabulate(columns, headers=["Column", "Type"], tablefmt="grid"))
        
        # Get total count
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cur.fetchone()[0]
        print(f"\nTotal entries: {total_count}")
        
        # Get count by date
        cur.execute(f"""
            SELECT DATE(scraped_at) as date, COUNT(*) as count
            FROM {table_name}
            GROUP BY DATE(scraped_at)
            ORDER BY date DESC
            LIMIT 5
        """)
        date_counts = cur.fetchall()
        print("\nEntries by date (last 5 days):")
        print(tabulate(date_counts, headers=["Date", "Count"], tablefmt="grid"))
        
        # Get most recent entries
        if db_name == "reddit_data":
            cur.execute(f"""
                SELECT subreddit, title, score, comments, scraped_at
                FROM {table_name}
                ORDER BY scraped_at DESC
                LIMIT 3
            """)
            recent = cur.fetchall()
            print("\nMost recent Reddit posts:")
           
        elif db_name == "tiktok_data":
            cur.execute(f"""
                SELECT author_username, description, likes, comments, scraped_at
                FROM {table_name}
                ORDER BY scraped_at DESC
                LIMIT 3
            """)
            recent = cur.fetchall()
            print("\nMost recent TikTok videos:")
            
        elif db_name == "youtube_data":
            cur.execute(f"""
                SELECT channel_title, title, view_count, like_count, scraped_at
                FROM {table_name}
                ORDER BY scraped_at DESC
                LIMIT 3
            """)
            recent = cur.fetchall()
            print("\nMost recent YouTube videos:")
          
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking {db_name}: {str(e)}")
        raise

def main():
    databases = ["reddit_data", "tiktok_data", "youtube_data"]
    for db in databases:
        check_database(db)

if __name__ == "__main__":
    main() 