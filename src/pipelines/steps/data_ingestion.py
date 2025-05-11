from zenml.steps import step
import pandas as pd
from pathlib import Path
import logging
from typing import Dict
from datetime import datetime, timedelta
import sqlite3

logger = logging.getLogger(__name__)

@step
def ingest_data() -> pd.DataFrame:
    """
    ZenML Step: Lädt, vereinheitlicht und kombiniert Social-Media-Daten
    aus der SQLite-Datenbank. Nur neue Einträge (basierend auf Timestamp)
    werden berücksichtigt.
    """
    logger.info("Starting data ingestion...")
    db_path = Path("data/social_media.db").resolve()
    processed_data_dir = Path("data/processed").resolve()
    processed_data_dir.mkdir(exist_ok=True)

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
        
        # --- TikTok ---
        logger.info("Processing TikTok data...")
        tiktok_query = """
        SELECT 
            id,
            description as content,
            author_username as author,
            likes,
            shares,
            comments,
            plays,
            created_time,
            scraped_at
        FROM tiktok_data
        """
        df_tiktok = pd.read_sql_query(tiktok_query, conn)
        if not df_tiktok.empty:
            df_tiktok['platform'] = 'tiktok'
            df_tiktok['engagement'] = df_tiktok[['likes', 'shares', 'comments']].fillna(0).sum(axis=1)
            df_tiktok['timestamp'] = pd.to_datetime(df_tiktok['created_time'], unit='s')
            logger.info(f"Processed TikTok data shape: {df_tiktok.shape}")
            dfs.append(df_tiktok)

        # --- YouTube ---
        logger.info("Processing YouTube data...")
        youtube_query = """
        SELECT 
            video_id as id,
            title,
            description as content,
            channel_title as author,
            view_count,
            like_count,
            comment_count,
            published_at,
            scraped_at
        FROM youtube_data
        """
        df_youtube = pd.read_sql_query(youtube_query, conn)
        if not df_youtube.empty:
            df_youtube['platform'] = 'youtube'
            df_youtube['engagement'] = df_youtube[['like_count', 'comment_count', 'view_count']].fillna(0).sum(axis=1)
            df_youtube['timestamp'] = pd.to_datetime(df_youtube['published_at'])
            logger.info(f"Processed YouTube data shape: {df_youtube.shape}")
            dfs.append(df_youtube)

        # --- Reddit ---
        logger.info("Processing Reddit data...")
        reddit_query = """
        SELECT 
            id,
            title,
            text as content,
            author,
            score,
            created_utc,
            num_comments,
            subreddit,
            scraped_at
        FROM reddit_data
        """
        df_reddit = pd.read_sql_query(reddit_query, conn)
        if not df_reddit.empty:
            df_reddit['platform'] = 'reddit'
            df_reddit['engagement'] = df_reddit[['score', 'num_comments']].fillna(0).sum(axis=1)
            df_reddit['timestamp'] = pd.to_datetime(df_reddit['created_utc'], unit='s')
            logger.info(f"Processed Reddit data shape: {df_reddit.shape}")
            dfs.append(df_reddit)

    except Exception as e:
        logger.error(f"Error accessing database: {str(e)}", exc_info=True)
        raise
    finally:
        conn.close()

    # Combine all dataframes
    if not dfs:
        logger.warning("No data found in the database.")
        return pd.DataFrame(columns=['platform', 'content', 'engagement', 'timestamp'])

    logger.info(f"Combining {len(dfs)} dataframes...")
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined data shape: {combined_df.shape}")

    # Drop duplicates and save the processed data
    combined_df = combined_df.drop_duplicates(subset=['content', 'timestamp'])
    logger.info(f"Final data shape after removing duplicates: {combined_df.shape}")

    output_file = processed_data_dir / "processed_data.csv"
    combined_df.to_csv(output_file, index=False)
    logger.info(f"Saved processed data to {output_file}")

    logger.info(f"Ingestion complete: {len(combined_df)} rows processed")
    return combined_df
