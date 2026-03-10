# FreelanceFeed by @duckb1t — duckb1t.cv
from typing import Iterator
from .base import BaseScraper, ScraperException
from models import Job
import requests
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger(__name__)

class PPHScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "PeoplePerHour"
        
    @property
    def env_toggle(self) -> str:
        return "ENABLE_PEOPLEPERHOUR"
        
    def scrape(self) -> Iterator[Job]:
        # PeoplePerHour public project search
        url = "https://www.peopleperhour.com/freelance-jobs"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
        except Exception as e:
            raise ScraperException(f"Failed to fetch or parse {self.name}: {e}")
            
        # PPH uses lists of jobs
        job_items = soup.find_all('li', class_='list-item')
        if not job_items:
             # Their classes change frequently, fallback check
             job_items = soup.find_all('div', class_=lambda c: c and 'project-item' in c.lower())
             
        for item in job_items:
            try:
                # Find title and link
                title_elem = item.find('a', class_=lambda c: c and 'title' in c.lower())
                if not title_elem:
                     title_elem = item.find('h6')
                     if title_elem:
                         title_elem = title_elem.find('a')
                         
                if not title_elem:
                     continue
                     
                title = title_elem.text.strip()
                link = title_elem.get('href', '')
                if link and not link.startswith('http'):
                     link = 'https://www.peopleperhour.com' + link
                     
                job_id = link.split('-')[-1].split('/')[0] if '-' in link else str(time.time())
                
                # Description
                desc_elem = item.find('div', class_=lambda c: c and 'description' in c.lower())
                description = desc_elem.text.strip() if desc_elem else 'No description provided.'
                
                # Budget
                budget_elem = item.find('div', class_=lambda c: c and 'price' in c.lower())
                budget_str = budget_elem.text.strip() if budget_elem else None
                
                yield Job(
                    id=f"pph_{job_id}",
                    platform=self.name,
                    title=title,
                    description=description,
                    url=link,
                    budget=budget_str
                )
                
            except Exception as e:
                logger.warning(f"Error parsing job from {self.name}: {e}")
                continue
