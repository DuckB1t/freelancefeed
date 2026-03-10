# FreelanceFeed by @duckb1t — duckb1t.cv
import requests
from typing import Iterator
from .base import BaseScraper, ScraperException
from models import Job
import time
import logging

logger = logging.getLogger(__name__)

class RemoteOKScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "RemoteOK"
        
    @property
    def env_toggle(self) -> str:
        return "ENABLE_REMOTEOK"
        
    def scrape(self) -> Iterator[Job]:
        # RemoteOK has a JSON API which makes it very easy
        url = "https://remoteok.com/api"
        headers = {
            "User-Agent": "FreelanceFeed Bot (https://duckb1t.cv)"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise ScraperException(f"Failed to fetch {self.name}: {e}")
            
        # The first item in RemoteOK's API is a legal/notice object, we skip it
        for idx, item in enumerate(data):
            if idx == 0 and "legal" in item:
                continue
                
            try:
                # Basic fields
                job_id = f"remoteok_{item.get('id', time.time())}"
                title = item.get('position', 'Unknown Title')
                company = item.get('company', 'Unknown Company')
                
                # RemoteOK has a lot of tags usually
                tags = item.get('tags', [])
                # Their description is sometimes HTML, but models str handles basic formatting
                description = item.get('description', '')
                
                # Format URL
                job_url = item.get('url', f"https://remoteok.com")
                
                # Add company to title for better context
                full_title = f"{title} at {company}"
                
                # Budget handling (RemoteOK provides salary_min and salary_max usually)
                min_sal = item.get('salary_min')
                max_sal = item.get('salary_max')
                budget_str = None
                if min_sal and max_sal:
                    budget_str = f"${min_sal:,} - ${max_sal:,} / yr"
                elif min_sal:
                    budget_str = f"From ${min_sal:,} / yr"
                elif max_sal:
                     budget_str = f"Up to ${max_sal:,} / yr"
                
                # Posted at 
                posted_date = item.get('date', '')
                if posted_date:
                    # Simple date formatting if available
                    posted_at = str(posted_date).split('T')[0]
                else:
                    posted_at = "Recently"
                
                yield Job(
                    id=job_id,
                    platform=self.name,
                    title=full_title,
                    description=description, # Can get very long, model handles truncating
                    url=job_url,
                    budget=budget_str,
                    tags=tags,
                    posted_at=posted_at
                )
            except Exception as e:
                logger.warning(f"Error parsing job from {self.name}: {e}")
                continue
