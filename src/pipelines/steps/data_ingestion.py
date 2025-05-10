from zenml.steps import step
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

@step
def load_social_media_data() -> Dict[str, pd.DataFrame]:
    """Load data from all social media platforms."""
    data_dir = Path("data/raw")
    data = {}
    
    # Load TikTok data
    tiktok_files = list(data_dir.glob("tiktok_*.csv"))
    if tiktok_files:
        tiktok_data = pd.concat([pd.read_csv(f) for f in tiktok_files])
        data["tiktok"] = tiktok_data
        logger.info(f"Loaded {len(tiktok_data)} TikTok records")
    
    # Load YouTube data
    youtube_files = list(data_dir.glob("youtube_*.csv"))
    if youtube_files:
        youtube_data = pd.concat([pd.read_csv(f) for f in youtube_files])
        data["youtube"] = youtube_data
        logger.info(f"Loaded {len(youtube_data)} YouTube records")
    
    # Load Reddit data
    reddit_files = list(data_dir.glob("reddit_*.csv"))
    if reddit_files:
        reddit_data = pd.concat([pd.read_csv(f) for f in reddit_files])
        data["reddit"] = reddit_data
        logger.info(f"Loaded {len(reddit_data)} Reddit records")
    
    return data

@step
def combine_social_media_data(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combine data from all social media platforms into a single DataFrame."""
    combined_data = []
    required_columns = ['platform', 'text', 'timestamp', 'engagement_score']
    
    for platform, df in data.items():
        # Add platform identifier
        df['platform'] = platform
        
        # Standardize column names
        if platform == 'tiktok':
            df = df.rename(columns={
                'description': 'text',
                'created_time': 'timestamp',
                'likes': 'engagement_score'
            })
        elif platform == 'youtube':
            df = df.rename(columns={
                'title': 'text',
                'published_at': 'timestamp',
                'view_count': 'engagement_score'
            })
        elif platform == 'reddit':
            df = df.rename(columns={
                'title': 'text',
                'created_utc': 'timestamp',
                'score': 'engagement_score'
            })
        
        # Ensure all required columns are present
        for col in required_columns:
            if col not in df.columns:
                df[col] = pd.NA
        
        # Select only the required columns
        df = df[required_columns]
        
        combined_data.append(df)
    
    # Combine all data
    final_df = pd.concat(combined_data, ignore_index=True)
    logger.info(f"Combined {len(final_df)} total records from all platforms")
    
    return final_df

@step
def run_data_ingestion() -> pd.DataFrame:
    """Main data ingestion step that runs scrapers and processes the data."""
    from src.scheduler.run_all_scrapers import run_all
    
    # Run all scrapers
    logger.info("Running all scrapers...")
    run_all()
    
    # Load and combine data
    logger.info("Loading and combining data...")
    raw_data = load_social_media_data()
    combined_data = combine_social_media_data(raw_data)
    
    return combined_data 