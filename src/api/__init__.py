"""
API Module for Social Media Trend Analysis

This package contains API endpoints for various parts of the application.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from models import get_db, RedditData, TikTokData, YouTubeData

logger = logging.getLogger(__name__)

api_router = APIRouter()

@api_router.get("/recent-data")
async def get_recent_data(platform: str = "reddit", limit: int = 10, db: Session = Depends(get_db)):
    """
    Get recent data from a specific platform
    """
    try:
        if platform == "reddit":
            data = db.query(RedditData).order_by(RedditData.created_utc.desc()).limit(limit).all()
            return [
                {
                    "id": item.id,
                    "title": item.title,
                    "text": item.text,
                    "author": item.author,
                    "score": item.score,
                    "created_at": item.created_utc,
                    "num_comments": item.num_comments,
                    "url": item.url,
                    "subreddit": item.subreddit,
                    "platform": "reddit"
                }
                for item in data
            ]
        elif platform == "tiktok":
            data = db.query(TikTokData).order_by(TikTokData.created_time.desc()).limit(limit).all()
            return [
                {
                    "id": item.id,
                    "description": item.description,
                    "author_username": item.author_username,
                    "author_id": item.author_id,
                    "likes": item.likes,
                    "shares": item.shares,
                    "comments": item.comments,
                    "plays": item.plays,
                    "video_url": item.video_url,
                    "created_at": item.created_time,
                    "platform": "tiktok"
                }
                for item in data
            ]
        elif platform == "youtube":
            data = db.query(YouTubeData).order_by(YouTubeData.published_at.desc()).limit(limit).all()
            return [
                {
                    "id": item.video_id,
                    "title": item.title,
                    "description": item.description,
                    "channel_title": item.channel_title,
                    "view_count": item.view_count,
                    "like_count": item.like_count,
                    "comment_count": item.comment_count,
                    "published_at": item.published_at,
                    "platform": "youtube"
                }
                for item in data
            ]
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    except Exception as e:
        logger.error(f"Error fetching recent data for {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@api_router.get("/scraper-status")
async def get_scraper_status():
    """
    Get the current status of all scrapers
    """
    try:
        # Mock response for now - this would typically be pulled from a database or service
        return {
            "reddit": {"running": False, "last_run": datetime.now().isoformat(), "next_run": (datetime.now() + timedelta(hours=1)).isoformat()},
            "tiktok": {"running": False, "last_run": datetime.now().isoformat(), "next_run": (datetime.now() + timedelta(hours=1)).isoformat()},
            "youtube": {"running": False, "last_run": datetime.now().isoformat(), "next_run": (datetime.now() + timedelta(hours=1)).isoformat()}
        }
    except Exception as e:
        logger.error(f"Error fetching scraper status: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@api_router.get("/daily-stats")
async def get_daily_stats(db: Session = Depends(get_db)):
    """
    Get daily statistics across all platforms
    """
    try:
        # Calculate stats
        reddit_count = db.query(RedditData).count()
        tiktok_count = db.query(TikTokData).count()
        youtube_count = db.query(YouTubeData).count()
        
        # Get today's date
        today = datetime.now().date()
        today_start = datetime(today.year, today.month, today.day)
        
        # Count today's posts
        reddit_today = db.query(RedditData).filter(RedditData.scraped_at >= today_start).count()
        tiktok_today = db.query(TikTokData).filter(TikTokData.scraped_at >= today_start).count()
        youtube_today = db.query(YouTubeData).filter(YouTubeData.scraped_at >= today_start).count()
        
        return {
            "total": {
                "reddit": reddit_count,
                "tiktok": tiktok_count,
                "youtube": youtube_count,
                "all": reddit_count + tiktok_count + youtube_count
            },
            "today": {
                "reddit": reddit_today,
                "tiktok": tiktok_today,
                "youtube": youtube_today,
                "all": reddit_today + tiktok_today + youtube_today
            }
        }
    except Exception as e:
        logger.error(f"Error fetching daily stats: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

__all__ = ["api_router"]
