# FreelanceFeed by @duckb1t — duckb1t.cv
from typing import List, Type, Dict, Any
import logging
import importlib
import pkgutil
import json

from .base import BaseScraper, ScraperException
from models import Job
from database import Database

logger = logging.getLogger(__name__)

def load_scrapers(config: dict) -> List[BaseScraper]:
    """Dynamically loads and instantiates enabled scrapers."""
    scrapers_list = []
    
    # Import all modules in the scrapers package
    import scrapers
    for _, module_name, _ in pkgutil.iter_modules(scrapers.__path__):
        if module_name == 'base':
            continue
            
        try:
            module = importlib.import_module(f'scrapers.{module_name}')
            
            # Find classes inheriting from BaseScraper
            for item_name in dir(module):
                item = getattr(module, item_name)
                if isinstance(item, type) and issubclass(item, BaseScraper) and item is not BaseScraper:
                    scraper_instance = item()
                    
                    # Check if enabled in config
                    env_toggle = scraper_instance.env_toggle
                    if config.get(env_toggle, False):
                        scrapers_list.append(scraper_instance)
                    else:
                        logger.debug(f"Scraper {scraper_instance.name} is disabled by config.")
                        
        except Exception as e:
            logger.error(f"Failed to load scraper module {module_name}: {e}")
            
    return scrapers_list

def run_scrapers_for_user(user_config: dict, db: Database) -> List[Job]:
    """Runs all scrapers enabled for a specific user, filters jobs, and returns new ones."""
    
    # enabled_platforms is a JSON string in the DB
    try:
        enabled_platforms = json.loads(user_config.get("enabled_platforms", "{}"))
    except Exception:
        enabled_platforms = {}
        
    scrapers_list = load_scrapers(enabled_platforms)
    
    if not scrapers_list:
        logger.warning(f"No scrapers are currently enabled for user {user_config.get('chat_id')}.")
        return []

    new_jobs = []
    
    # Parse keywords from JSON
    try:
        keywords = json.loads(user_config.get("keywords", "[]"))
    except Exception:
        keywords = []
        
    try:
        exclude_keywords = json.loads(user_config.get("exclude_keywords", "[]"))
    except Exception:
        exclude_keywords = []
        
    min_budget = user_config.get("min_budget", 0)
    chat_id = user_config.get("chat_id")

    for scraper in scrapers_list:
        print(f"Scraping {scraper.name}...", end=" ", flush=True)
        try:
            found_count = 0
            for job in scraper.scrape():
                
                # Deduplication check FIRST (fastest) - per user now
                if db.is_job_seen(job.id, chat_id):
                    continue
                    
                # Keyword matching
                if not job.matches_keywords(keywords):
                    db.mark_job_seen(job.id, platform=job.platform, chat_id=chat_id) # Mark seen even if filtered
                    continue
                    
                if job.contains_excluded_keywords(exclude_keywords):
                    db.mark_job_seen(job.id, platform=job.platform, chat_id=chat_id)
                    continue
                    
                # Budget check (rudimentary, relies on scrapers converting to float/int if possible)
                if min_budget > 0 and job.budget:
                    try:
                        # Very simple budget check, can be refined based on how scrapers provide budget
                        budget_str = str(job.budget).replace('$', '').replace(',', '').strip()
                        budget_vals = [int(s) for s in budget_str.split() if s.isdigit()]
                        if budget_vals and max(budget_vals) < min_budget:
                             db.mark_job_seen(job.id, platform=job.platform, chat_id=chat_id)
                             continue
                    except Exception:
                        pass # Ignore budget parsing errors for now
                
                # If it passed all filters, it's a new, relevant job!
                new_jobs.append(job)
                db.mark_job_seen(job.id, platform=job.platform, chat_id=chat_id)
                found_count += 1
                
            print(f"[{found_count} new]")
            
        except Exception as e:
            logger.error(f"Error scraping {scraper.name}: {e}")
            print("[FAILED]")
            
    return new_jobs
