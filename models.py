# FreelanceFeed by @duckb1t — duckb1t.cv
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Job:
    """Represents a single freelance job listing."""
    id: str  # Unique identifier (e.g., URL or platform-specific ID)
    platform: str
    title: str
    description: str
    url: str
    budget: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    posted_at: str = "Recently"
    
    def matches_keywords(self, keywords: list[str]) -> bool:
        """Checks if the job title or description matches any of the given keywords."""
        if not keywords:
            return True # If no keywords are set, everything matches
        
        search_text = f"{self.title} {self.description}".lower()
        return any(keyword.lower() in search_text for keyword in keywords)
        
    def contains_excluded_keywords(self, exclude_keywords: list[str]) -> bool:
        """Checks if the job title or description contains any excluded keywords."""
        if not exclude_keywords:
            return False
            
        search_text = f"{self.title} {self.description}".lower()
        return any(keyword.lower() in search_text for keyword in exclude_keywords)
        
    def __str__(self):
        """Formats the job for Telegram message."""
        tags_str = ", ".join(self.tags) if self.tags else "None"
        budget_str = self.budget if self.budget else "N/A"
        
        # Truncate description to ~200 chars cleanly
        desc = self.description.replace('\n', ' ').strip()
        if len(desc) > 200:
            desc = desc[:197] + "..."
            
        return (
            f"[{self.platform.upper()}] // NEW JOB\n\n"
            f"{self.title}\n"
            f"{desc}\n\n"
            f"Budget  : {budget_str}\n"
            f"Tags    : {tags_str}\n"
            f"Posted  : {self.posted_at}\n\n"
            f"Apply → {self.url}"
        )
