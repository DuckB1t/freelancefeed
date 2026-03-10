# FreelanceFeed by @duckb1t — duckb1t.cv
from abc import ABC, abstractmethod
from typing import Iterator
import logging
from models import Job

logger = logging.getLogger(__name__)

class ScraperException(Exception):
    """Base exception for scraper errors."""
    pass

class BaseScraper(ABC):
    """Base class for all platform scrapers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the platform (e.g., 'RemoteOK')."""
        pass

    @property
    @abstractmethod
    def env_toggle(self) -> str:
        """The .env key to check if this scraper is enabled (e.g., 'ENABLE_REMOTEOK')."""
        pass
        
    @abstractmethod
    def scrape(self) -> Iterator[Job]:
        """
        Scrape the platform and yield Job objects.
        Should handle its own standard errors and raise ScraperException for fatal ones.
        """
        pass
        
    def __str__(self):
        return f"{self.name} Scraper"
