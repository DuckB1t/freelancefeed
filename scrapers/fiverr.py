# FreelanceFeed by @duckb1t — duckb1t.cv
from typing import Iterator
from .base import BaseScraper, ScraperException
from models import Job
import requests
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger(__name__)

class FiverrScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "Fiverr"
        
    @property
    def env_toggle(self) -> str:
        return "ENABLE_FIVERR"
        
    def scrape(self) -> Iterator[Job]:
        # Fiverr's "Buyer Requests" or job board is heavily authenticated.
        # Without login, it's very difficult to scrape direct "jobs".
        # As per prompt "if possible without login, otherwise skip for now"
        # We will attempt a generic search if there's a public interface, 
        # but mostly Fiverr is gig-based (freelancers post gigs, not jobs).
        # We will log a warning and return empty to fulfill the skip requirement gracefully.
        
        logger.info(f"{self.name} scraper skipping: requires login for buyer requests.")
        url = "https://www.fiverr.com/pages/auth" # Dummy URL just for structure
        
        # Empty iterator
        return iter([])

