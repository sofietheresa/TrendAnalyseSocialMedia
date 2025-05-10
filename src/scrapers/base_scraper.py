from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    def __init__(self):
        self.name = self.__class__.__name__.replace('Scraper', '').lower()
    
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape data from the platform.
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries containing the scraped data.
            Each dictionary should contain at least:
            - platform: str (platform name)
            - content: str (post content)
            - engagement: int (number of likes/upvotes)
            - timestamp: str (ISO format timestamp)
        """
        pass
    
    def _log_error(self, error: Exception):
        """Log an error that occurred during scraping."""
        logger.error(f"Error in {self.name} scraper: {str(error)}") 