from datetime import datetime
from typing import List, Dict, Any
from .base_scraper import BaseScraper

class YouTubeScraper(BaseScraper):
    """Scraper for YouTube data."""
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape data from YouTube.
        For testing purposes, returns mock data.
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing mock YouTube data.
        """
        # Mock data for testing
        mock_data = [
            {
                "platform": "youtube",
                "content": "How to Make the Perfect Chocolate Cake | Easy Recipe Tutorial",
                "engagement": 2500,
                "timestamp": datetime.now().isoformat(),
                "author": "baking_master",
                "views": 10000,
                "comments": 500,
                "duration": "15:30"
            },
            {
                "platform": "youtube",
                "content": "10 Tips for Better Photography | Beginner's Guide",
                "engagement": 1800,
                "timestamp": datetime.now().isoformat(),
                "author": "photo_pro",
                "views": 8000,
                "comments": 300,
                "duration": "12:45"
            }
        ]
        
        return mock_data 