from zenml.steps import step
import pandas as pd
from pathlib import Path
import logging
from typing import Dict
from datetime import datetime, timedelta
import sqlite3
import os

logger = logging.getLogger(__name__)

@step
def ingest_data() -> pd.DataFrame:
    """
    ZenML Step: Lädt, vereinheitlicht und kombiniert Social-Media-Daten
    aus der SQLite-Datenbank. Nur neue Einträge (basierend auf Timestamp)
    werden berücksichtigt.
    """
    logger.info("Starting data ingestion...")
    
    # Check if database exists
    db_path = Path("data/social_media.db").resolve()
    if not db_path.exists():
        logger.warning(f"Database file does not exist at: {db_path}")
        # Create empty directory structure
        processed_data_dir = Path("data/processed").resolve()
        processed_data_dir.mkdir(parents=True, exist_ok=True)
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['platform', 'content', 'engagement', 'timestamp'])
    
    processed_data_dir = Path("data/processed").resolve()
    processed_data_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Connecting to database at: {db_path}")

    last_run_file = processed_data_dir / "last_run_timestamp.txt"
    if last_run_file.exists():
        with open(last_run_file, "r") as f:
            last_run = datetime.fromisoformat(f.read().strip())
        logger.info(f"Last run timestamp: {last_run}")
    else:
        last_run = datetime.now() - timedelta(hours=24)
        logger.info(f"No last run file found, using default timestamp: {last_run}")

    dfs = []

    try:
        conn = sqlite3.connect(db_path)
        
        # Get all tables in the database to check what exists
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql_query(tables_query, conn)
        existing_tables = tables['name'].tolist()
        logger.info(f"Found tables in database: {existing_tables}")
        
        # --- TikTok ---
        if 'tiktok_data' in existing_tables:
            logger.info("Processing TikTok data...")
            # First check what columns are available
            columns_query = f"PRAGMA table_info(tiktok_data);"
            columns = pd.read_sql_query(columns_query, conn)
            column_names = columns['name'].tolist()
            
            # Construct query based on available columns
            tiktok_select = []
            if 'id' in column_names:
                tiktok_select.append('id')
            else:
                tiktok_select.append("'unknown' as id")
                
            if 'description' in column_names:
                tiktok_select.append('description as content')
            elif 'text' in column_names:
                tiktok_select.append('text as content')
            else:
                tiktok_select.append("'' as content")
                
            if 'author_username' in column_names:
                tiktok_select.append('author_username as author')
            elif 'author' in column_names:
                tiktok_select.append('author')
            else:
                tiktok_select.append("'unknown' as author")
                
            # Add engagement columns if they exist
            engagement_cols = []
            for col in ['likes', 'shares', 'comments', 'plays']:
                if col in column_names:
                    engagement_cols.append(col)
                    tiktok_select.append(col)
                    
            # Add date columns
            date_col = ''
            if 'created_time' in column_names:
                tiktok_select.append('created_time')
                date_col = 'created_time'
            elif 'created_at' in column_names:
                tiktok_select.append('created_at')
                date_col = 'created_at'
                
            if 'scraped_at' in column_names:
                tiktok_select.append('scraped_at')
            
            if tiktok_select and date_col:
                tiktok_query = f"SELECT {', '.join(tiktok_select)} FROM tiktok_data"
                df_tiktok = pd.read_sql_query(tiktok_query, conn)
                
                if not df_tiktok.empty:
                    df_tiktok['platform'] = 'tiktok'
                    # Calculate engagement based on available columns
                    if engagement_cols:
                        df_tiktok['engagement'] = df_tiktok[engagement_cols].fillna(0).sum(axis=1)
                    else:
                        df_tiktok['engagement'] = 0
                        
                    # Process timestamp based on available column
                    if date_col == 'created_time':
                        df_tiktok['timestamp'] = pd.to_datetime(df_tiktok['created_time'], unit='s', errors='coerce')
                    else:
                        df_tiktok['timestamp'] = pd.to_datetime(df_tiktok[date_col], errors='coerce')
                        
                    logger.info(f"Processed TikTok data shape: {df_tiktok.shape}")
                    dfs.append(df_tiktok)
            else:
                logger.warning("Required columns for TikTok not found, skipping")

        # --- YouTube ---
        if 'youtube_data' in existing_tables:
            logger.info("Processing YouTube data...")
            # Check columns
            columns_query = f"PRAGMA table_info(youtube_data);"
            columns = pd.read_sql_query(columns_query, conn)
            column_names = columns['name'].tolist()
            
            # Construct query based on available columns
            youtube_select = []
            if 'video_id' in column_names:
                youtube_select.append('video_id as id')
            elif 'id' in column_names:
                youtube_select.append('id')
            else:
                youtube_select.append("'unknown' as id")
                
            if 'title' in column_names:
                youtube_select.append('title')
                
            if 'description' in column_names:
                youtube_select.append('description as content')
            elif 'content' in column_names:
                youtube_select.append('content')
            else:
                youtube_select.append("'' as content")
                
            if 'channel_title' in column_names:
                youtube_select.append('channel_title as author')
            elif 'author' in column_names:
                youtube_select.append('author')
            else:
                youtube_select.append("'unknown' as author")
                
            # Add engagement columns if they exist
            engagement_cols = []
            for col in ['view_count', 'like_count', 'comment_count']:
                if col in column_names:
                    engagement_cols.append(col)
                    youtube_select.append(col)
                    
            # Add date columns
            date_col = ''
            if 'published_at' in column_names:
                youtube_select.append('published_at')
                date_col = 'published_at'
            elif 'created_at' in column_names:
                youtube_select.append('created_at')
                date_col = 'created_at'
                
            if 'scraped_at' in column_names:
                youtube_select.append('scraped_at')
            
            if youtube_select and date_col:
                youtube_query = f"SELECT {', '.join(youtube_select)} FROM youtube_data"
                df_youtube = pd.read_sql_query(youtube_query, conn)
                
                if not df_youtube.empty:
                    df_youtube['platform'] = 'youtube'
                    # Calculate engagement based on available columns
                    if engagement_cols:
                        df_youtube['engagement'] = df_youtube[engagement_cols].fillna(0).sum(axis=1)
                    else:
                        df_youtube['engagement'] = 0
                        
                    # Process timestamp
                    df_youtube['timestamp'] = pd.to_datetime(df_youtube[date_col], errors='coerce')
                    logger.info(f"Processed YouTube data shape: {df_youtube.shape}")
                    dfs.append(df_youtube)
            else:
                logger.warning("Required columns for YouTube not found, skipping")

        # --- Reddit ---
        if 'reddit_data' in existing_tables:
            logger.info("Processing Reddit data...")
            # Check columns
            columns_query = f"PRAGMA table_info(reddit_data);"
            columns = pd.read_sql_query(columns_query, conn)
            column_names = columns['name'].tolist()
            
            # Construct query based on available columns
            reddit_select = []
            if 'id' in column_names:
                reddit_select.append('id')
            else:
                reddit_select.append("'unknown' as id")
                
            if 'title' in column_names:
                reddit_select.append('title')
                
            # Try different possible content column names
            content_col = ''
            if 'text' in column_names:
                reddit_select.append('text as content')
                content_col = 'text'
            elif 'body' in column_names:
                reddit_select.append('body as content')
                content_col = 'body'
            elif 'selftext' in column_names:
                reddit_select.append('selftext as content')
                content_col = 'selftext'
            elif 'content' in column_names:
                reddit_select.append('content')
                content_col = 'content'
            else:
                reddit_select.append("'' as content")
                content_col = ''
                
            if 'author' in column_names:
                reddit_select.append('author')
            else:
                reddit_select.append("'unknown' as author")
                
            # Add engagement columns if they exist
            engagement_cols = []
            for col in ['score', 'num_comments']:
                if col in column_names:
                    engagement_cols.append(col)
                    reddit_select.append(col)
                    
            # Add date columns
            date_col = ''
            if 'created_utc' in column_names:
                reddit_select.append('created_utc')
                date_col = 'created_utc'
            elif 'created' in column_names:
                reddit_select.append('created')
                date_col = 'created'
            elif 'created_at' in column_names:
                reddit_select.append('created_at')
                date_col = 'created_at'
                
            if 'subreddit' in column_names:
                reddit_select.append('subreddit')
                
            if 'scraped_at' in column_names:
                reddit_select.append('scraped_at')
            
            if reddit_select and (content_col or 'title' in column_names) and date_col:
                reddit_query = f"SELECT {', '.join(reddit_select)} FROM reddit_data"
                df_reddit = pd.read_sql_query(reddit_query, conn)
                
                if not df_reddit.empty:
                    df_reddit['platform'] = 'reddit'
                    # Calculate engagement based on available columns
                    if engagement_cols:
                        df_reddit['engagement'] = df_reddit[engagement_cols].fillna(0).sum(axis=1)
                    else:
                        df_reddit['engagement'] = 0
                        
                    # Process timestamp based on available column
                    if date_col == 'created_utc' or date_col == 'created':
                        df_reddit['timestamp'] = pd.to_datetime(df_reddit[date_col], unit='s', errors='coerce')
                    else:
                        df_reddit['timestamp'] = pd.to_datetime(df_reddit[date_col], errors='coerce')
                        
                    logger.info(f"Processed Reddit data shape: {df_reddit.shape}")
                    dfs.append(df_reddit)
            else:
                logger.warning("Required columns for Reddit not found, skipping")

    except Exception as e:
        logger.error(f"Error accessing database: {str(e)}", exc_info=True)
        # If an error occurs, create an empty DataFrame with the expected columns
        return pd.DataFrame(columns=['platform', 'content', 'engagement', 'timestamp'])
    finally:
        conn.close()

    # Combine all dataframes
    if not dfs:
        logger.warning("No data found in the database.")
        return pd.DataFrame(columns=['platform', 'content', 'engagement', 'timestamp'])

    logger.info(f"Combining {len(dfs)} dataframes...")
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined data shape: {combined_df.shape}")

    # Ensure all required columns exist
    if 'content' not in combined_df.columns:
        combined_df['content'] = ''
    if 'engagement' not in combined_df.columns:
        combined_df['engagement'] = 0
    if 'timestamp' not in combined_df.columns:
        combined_df['timestamp'] = pd.NaT

    # Drop duplicates and save the processed data
    combined_df = combined_df.drop_duplicates(subset=['content', 'timestamp'])
    logger.info(f"Final data shape after removing duplicates: {combined_df.shape}")

    # Ensure timestamp is in datetime format
    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], errors='coerce')
    # Drop rows with invalid timestamps
    if combined_df['timestamp'].isna().any():
        logger.warning(f"Dropping {combined_df['timestamp'].isna().sum()} rows with invalid timestamps")
        combined_df = combined_df.dropna(subset=['timestamp'])

    # Save timestamp of this run
    with open(last_run_file, "w") as f:
        f.write(datetime.now().isoformat())

    output_file = processed_data_dir / "processed_data.csv"
    combined_df.to_csv(output_file, index=False)
    logger.info(f"Saved processed data to {output_file}")

    logger.info(f"Ingestion complete: {len(combined_df)} rows processed")
    return combined_df
