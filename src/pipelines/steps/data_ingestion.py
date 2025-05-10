from zenml.steps import step
import pandas as pd
from pathlib import Path
import logging
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@step
def ingest_data() -> pd.DataFrame:
    """
    ZenML Step: Lädt, vereinheitlicht und kombiniert Social-Media-Daten
    aus CSV-Dateien im Verzeichnis `data/raw`. Nur neue Einträge
    (basierend auf Timestamp) werden berücksichtigt.
    """
    logger.info("Starting data ingestion...")
    raw_data_dir = Path("data/raw").resolve()
    processed_data_dir = Path("data/processed").resolve()
    processed_data_dir.mkdir(exist_ok=True)

    logger.info(f"Looking for data files in: {raw_data_dir}")
    logger.info(f"Available files: {list(raw_data_dir.glob('*.csv'))}")

    last_run_file = processed_data_dir / "last_run_timestamp.txt"
    if last_run_file.exists():
        with open(last_run_file, "r") as f:
            last_run = datetime.fromisoformat(f.read().strip())
        logger.info(f"Last run timestamp: {last_run}")
    else:
        last_run = datetime.now() - timedelta(hours=24)
        logger.info(f"No last run file found, using default timestamp: {last_run}")

    dfs = []

    # --- TikTok ---
    for file in raw_data_dir.glob("tiktok_*.csv"):
        try:
            logger.info(f"Processing TikTok file: {file}")
            df = pd.read_csv(file)
            logger.info(f"Raw TikTok data shape: {df.shape}")
            df['platform'] = 'tiktok'
            df['content'] = df.get('description', pd.Series("")).fillna('')
            
            # Handle string-to-float conversion for engagement metrics
            for col in ['likes', 'shares', 'comments']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            df['engagement'] = df[['likes', 'shares', 'comments']].fillna(0).sum(axis=1)
            df['timestamp'] = pd.to_datetime(df.get('created_time', None), unit='s', errors='coerce')
            logger.info(f"Processed TikTok data shape: {df.shape}")
            dfs.append(df)
        except Exception as e:
            logger.error(f"Error processing TikTok file {file}: {str(e)}", exc_info=True)

    # --- YouTube ---
    for file in raw_data_dir.glob("youtube_*.csv"):
        try:
            logger.info(f"Processing YouTube file: {file}")
            df = pd.read_csv(file)
            logger.info(f"Raw YouTube data shape: {df.shape}")
            df['platform'] = 'youtube'
            df['content'] = df.get('description', pd.Series("")).fillna('')
            
            # Handle string-to-float conversion for engagement metrics
            for col in ['like_count', 'comment_count']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            df['engagement'] = df[['like_count', 'comment_count']].fillna(0).sum(axis=1)
            df['timestamp'] = pd.to_datetime(df.get('published_at', None), errors='coerce')
            logger.info(f"Processed YouTube data shape: {df.shape}")
            dfs.append(df)
        except Exception as e:
            logger.error(f"Error processing YouTube file {file}: {str(e)}", exc_info=True)

    # --- Reddit ---
    for file in raw_data_dir.glob("reddit_*.csv"):
        try:
            logger.info(f"Processing Reddit file: {file}")
            df = pd.read_csv(file)
            logger.info(f"Raw Reddit data shape: {df.shape}")
            df['platform'] = 'reddit'
            df['content'] = df.get('text', pd.Series("")).fillna('')
            
            # Handle string-to-float conversion for engagement metrics
            for col in ['score', 'comments']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            df['engagement'] = df[['score', 'comments']].fillna(0).sum(axis=1)
            df['timestamp'] = pd.to_datetime(df.get('created', None), errors='coerce')
            logger.info(f"Processed Reddit data shape: {df.shape}")
            dfs.append(df)
        except Exception as e:
            logger.error(f"Error processing Reddit file {file}: {str(e)}", exc_info=True)

    if not dfs:
        logger.warning("No data sources could be loaded successfully.")
        return pd.DataFrame(columns=['platform', 'content', 'engagement', 'timestamp'])

    logger.info(f"Combining {len(dfs)} dataframes...")
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined data shape before filtering: {combined_df.shape}")

    # Log null values in timestamp column
    null_timestamps = combined_df['timestamp'].isnull().sum()
    logger.info(f"Number of null timestamps: {null_timestamps}")

    combined_df.dropna(subset=['timestamp'], inplace=True)
    logger.info(f"Data shape after dropping null timestamps: {combined_df.shape}")

    # Ensure all timestamps are timezone-naive
    if not combined_df.empty:
        combined_df['timestamp'] = combined_df['timestamp'].apply(lambda x: x.tz_localize(None) if pd.notnull(x) and hasattr(x, 'tzinfo') and x.tzinfo is not None else x)
        if last_run.tzinfo is not None:
            last_run = last_run.replace(tzinfo=None)

    # Log timestamp range
    if not combined_df.empty:
        logger.info(f"Timestamp range: {combined_df['timestamp'].min()} to {combined_df['timestamp'].max()}")
        logger.info(f"Last run timestamp: {last_run}")
        
        # Log distribution of timestamps
        time_diff = (combined_df['timestamp'] - last_run).dt.total_seconds()
        logger.info(f"Number of rows newer than last run: {(time_diff > 0).sum()}")
        logger.info(f"Number of rows older than last run: {(time_diff <= 0).sum()}")
        
        # For testing, let's process all data if it's the first run
        if not last_run_file.exists():
            logger.info("First run detected - processing all available data")
            combined_df = combined_df.copy()
        else:
            combined_df = combined_df[combined_df['timestamp'] > last_run]
            logger.info(f"Data shape after filtering by last run: {combined_df.shape}")

    combined_df = combined_df.drop_duplicates(subset=['content', 'timestamp'])
    logger.info(f"Final data shape after removing duplicates: {combined_df.shape}")

    # Save the processed data
    output_file = processed_data_dir / "processed_data.csv"
    combined_df.to_csv(output_file, index=False)
    logger.info(f"Saved processed data to {output_file}")

    # Update last run timestamp
    with open(last_run_file, "w") as f:
        f.write(datetime.now().isoformat())

    logger.info(f"Ingestion complete: {len(combined_df)} rows after filtering")
    logger.info(f"Final DataFrame shape: {combined_df.shape}")
    logger.info(f"Final DataFrame head:\n{combined_df.head()}\nColumns: {list(combined_df.columns)}")
    return combined_df
