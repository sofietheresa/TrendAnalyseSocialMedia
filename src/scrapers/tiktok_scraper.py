from datetime import datetime
from typing import List, Dict, Any
from .base_scraper import BaseScraper

class TikTokScraper(BaseScraper):
    """Scraper for TikTok data."""
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape data from TikTok.
        For testing purposes, returns mock data.
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing mock TikTok data.
        """
        # Mock data for testing
        mock_data = [
            {
                "platform": "tiktok",
                "content": "Check out this amazing dance video! #dance #viral",
                "engagement": 1500,
                "timestamp": datetime.now().isoformat(),
                "author": "dance_creator",
                "views": 5000,
                "comments": 200
            },
            {
                "platform": "tiktok",
                "content": "Life hack: How to organize your closet in 5 minutes #organization #lifehack",
                "engagement": 800,
                "timestamp": datetime.now().isoformat(),
                "author": "organize_pro",
                "views": 3000,
                "comments": 150
            }
        ]
        
        return mock_data 