# FreelanceFeed by @duckb1t — duckb1t.cv
from typing import Iterator
from .base import BaseScraper, ScraperException
from models import Job
import requests
import xml.etree.ElementTree as ET
import html
import re
import time
import logging

logger = logging.getLogger(__name__)

class GuruScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "Guru"
        
    @property
    def env_toggle(self) -> str:
        return "ENABLE_GURU"
        
    def scrape(self) -> Iterator[Job]:
        # Guru RSS feed 
        # Note: Guru often changes or hides their RSS feeds.
        url = "https://www.guru.com/rss/jobs/freelance-jobs/" # Trying a more specific path
        
        headers = {
            "User-Agent": "FreelanceFeed Bot (https://duckb1t.cv)"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                logger.warning(f"Guru RSS feed not found (404) at {url}. They may have removed it.")
                return # Yield nothing gracefully
            raise ScraperException(f"HTTP Error fetching {self.name}: {e}")
        except Exception as e:
            raise ScraperException(f"Failed to fetch or parse {self.name}: {e}")
            
        for item in root.findall('.//item'):
            try:
                title = item.findtext('title', 'Unknown Title')
                link = item.findtext('link', '')
                
                # Guru links look like: https://www.guru.com/jobs/job-title/job-id
                job_id = link.rstrip('/').split('/')[-1] if link else str(time.time())
                pub_date = item.findtext('pubDate', 'Recently')
                
                raw_desc = item.findtext('description', '')
                desc_text = html.unescape(raw_desc)
                desc_clean = re.sub(r'<[^>]+>', ' ', desc_text)
                desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
                
                yield Job(
                    id=f"guru_{job_id}",
                    platform=self.name,
                    title=title,
                    description=desc_clean,
                    url=link,
                    posted_at=pub_date
                )
                
            except Exception as e:
                logger.warning(f"Error parsing job from {self.name}: {e}")
                continue
