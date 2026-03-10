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

class FreelancerScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "Freelancer"
        
    @property
    def env_toggle(self) -> str:
        return "ENABLE_FREELANCER"
        
    def scrape(self) -> Iterator[Job]:
        # Freelancer also has an RSS feed
        url = "https://www.freelancer.com/rss.xml"
        
        headers = {
            "User-Agent": "FreelanceFeed Bot (https://duckb1t.cv)"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            
        except requests.exceptions.HTTPError as e:
            raise ScraperException(f"HTTP Error fetching {self.name}: {e}")
        except Exception as e:
            raise ScraperException(f"Failed to fetch or parse {self.name}: {e}")
            
        for item in root.findall('.//item'):
            try:
                title = item.findtext('title', 'Unknown Title')
                link = item.findtext('link', '')
                job_id = link.split('/')[-1] if link else str(time.time())
                pub_date = item.findtext('pubDate', 'Recently')
                
                raw_desc = item.findtext('description', '')
                desc_text = html.unescape(raw_desc)
                desc_clean = re.sub(r'<[^>]+>', ' ', desc_text)
                desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
                
                # Freelancer titles often include budget like "Build a website - $50-$100"
                # But it's unstructured. 
                
                yield Job(
                    id=f"freelancer_{job_id}",
                    platform=self.name,
                    title=title,
                    description=desc_clean,
                    url=link,
                    posted_at=pub_date
                )
                
            except Exception as e:
                logger.warning(f"Error parsing job from {self.name}: {e}")
                continue
