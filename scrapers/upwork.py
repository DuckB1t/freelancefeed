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

class UpworkScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "Upwork"
        
    @property
    def env_toggle(self) -> str:
        return "ENABLE_UPWORK"
        
    def scrape(self) -> Iterator[Job]:
        # Upwork has an RSS feed for searches. We can construct a broad one
        # or just grab the recent jobs. To make it broad without auth, we'll
        # use a general search RSS.
        # Note: Upwork RSS sometimes restricts broad zero-keyword searches,
        # but we can try a few common categories if a pure blank search fails.
        # For this example, we use a generic recent feed.
        
        # We can also pull keywords from config to build targeted RSS feeds, 
        # but a general feed is sufficient for MVP filtering.
        
        # A common trick for Upwork RSS is searching for a very common character like 'a'
        # or just hitting the base RSS if permitted.
        url = "https://www.upwork.com/ab/feed/jobs/rss?sort=recency"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            # Upwork often returns 403 for automated generic RSS without a specific search query
            # If so, we'll try a fallback query from a common programming term
            if response.status_code == 403:
                logger.debug("Upwork returned 403 for generic RSS. Trying fallback query 'developer'.")
                url = "https://www.upwork.com/ab/feed/jobs/rss?q=developer&sort=recency"
                response = requests.get(url, headers=headers, timeout=15)
                
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                 logger.warning("Upwork RSS is actively blocking this IP/Agent. Try using a personal RSS link in the future.")
                 return # Just return empty iterator instead of crashing
            raise ScraperException(f"HTTP Error fetching {self.name}: {e}")
            
        except Exception as e:
            raise ScraperException(f"Failed to fetch or parse {self.name}: {e}")
            
        for item in root.findall('.//item'):
            try:
                title = item.findtext('title', 'Unknown Title')
                # Upwork titles often end with ' - Upwork', clean it
                title = re.sub(r'\s*-\s*Upwork$', '', title)
                
                link = item.findtext('link', '')
                job_id = link.split('~')[-1].split('?')[0] if '~' in link else str(time.time())
                
                pub_date = item.findtext('pubDate', 'Recently')
                
                # Upwork puts budget wrapped in HTML usually in the description
                raw_desc = item.findtext('description', '')
                desc_text = html.unescape(raw_desc)
                
                # Cleanup HTML tags from description
                desc_clean = re.sub(r'<[^>]+>', ' ', desc_text)
                desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
                
                # Try to extract budget
                budget_str = None
                budget_match = re.search(r'Budget\s*:\s*\$?([0-9,]+)', desc_text, re.IGNORECASE)
                hourly_match = re.search(r'Hourly Range\s*:\s*\$?([0-9.,]+)\s*-\s*\$?([0-9.,]+)', desc_text, re.IGNORECASE)
                
                if budget_match:
                    budget_str = f"${budget_match.group(1)} (Fixed)"
                elif hourly_match:
                    budget_str = f"${hourly_match.group(1)} - ${hourly_match.group(2)} / hr"
                
                yield Job(
                    id=f"upwork_{job_id}",
                    platform=self.name,
                    title=title,
                    description=desc_clean,
                    url=link,
                    budget=budget_str,
                    posted_at=pub_date
                )
                
            except Exception as e:
                logger.warning(f"Error parsing job from {self.name}: {e}")
                continue
