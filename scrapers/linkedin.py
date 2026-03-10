# FreelanceFeed by @duckb1t — duckb1t.cv
from typing import Iterator
from .base import BaseScraper, ScraperException
from models import Job
import requests
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger(__name__)

class LinkedInScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "LinkedIn"
        
    @property
    def env_toggle(self) -> str:
        return "ENABLE_LINKEDIN"
        
    def scrape(self) -> Iterator[Job]:
        # LinkedIn has a public job search page that doesn't require login for the first few pages
        # We search for "freelance" or "contract" globally
        url = "https://www.linkedin.com/jobs/search/?keywords=freelance&f_WT=2&position=1&pageNum=0"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning(f"LinkedIn rate limited us (429).")
                return
            raise ScraperException(f"HTTP Error fetching {self.name}: {e}")
        except Exception as e:
            raise ScraperException(f"Failed to fetch or parse {self.name}: {e}")
            
        job_cards = soup.find_all('div', class_='base-card')
        
        for card in job_cards:
            try:
                title_elem = card.find('h3', class_='base-search-card__title')
                title = title_elem.text.strip() if title_elem else 'Unknown Title'
                
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                company = company_elem.text.strip() if company_elem else 'Unknown Company'
                
                link_elem = card.find('a', class_='base-card__full-link')
                if not link_elem:
                   link_elem = card.find('a', class_='base-search-card__title')
                   
                raw_url = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ''
                
                # Clean tracking params from URL
                job_url = raw_url.split('?')[0] if '?' in raw_url else raw_url
                
                job_id = card.get('data-entity-urn', '').split(':')[-1]
                if not job_id:
                     job_id = str(time.time())
                     
                date_elem = card.find('time')
                posted_at = date_elem.text.strip() if date_elem else "Recently"
                
                # LinkedIn public search doesn't give full descriptions or budget on the list page
                # We would have to fetch each job URL individually which will get us rate limited quickly
                description = f"Job at {company}. (View link for full description)"
                full_title = f"{title} at {company}"
                
                yield Job(
                    id=f"linkedin_{job_id}",
                    platform=self.name,
                    title=full_title,
                    description=description,
                    url=job_url,
                    posted_at=posted_at
                )
                
            except Exception as e:
                logger.warning(f"Error parsing job from {self.name}: {e}")
                continue
