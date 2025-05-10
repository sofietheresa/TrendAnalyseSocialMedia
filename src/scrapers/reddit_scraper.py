from datetime import datetime
from typing import List, Dict, Any
from .base_scraper import BaseScraper

class RedditScraper(BaseScraper):
    """Scraper for Reddit data."""
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape data from Reddit.
        For testing purposes, returns mock data.
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing mock Reddit data.
        """
        # Mock data for testing
        mock_data = [
            {
                "platform": "reddit",
                "content": "TIL that honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
                "engagement": 12000,
                "timestamp": datetime.now().isoformat(),
                "author": "history_buff",
                "subreddit": "todayilearned",
                "comments": 800,
                "awards": 5
            },
            {
                "platform": "reddit",
                "content": "My cat's reaction when I try to work from home",
                "engagement": 8000,
                "timestamp": datetime.now().isoformat(),
                "author": "cat_lover",
                "subreddit": "aww",
                "comments": 400,
                "awards": 3
            }
        ]
        
        return mock_data 