# FreelanceFeed by @duckb1t — duckb1t.cv
import sqlite3
import datetime
import logging
import json
import typing
from config import load_config

logger = logging.getLogger(__name__)

class Database:
    """Handles storage of seen jobs and the 30-day cleanup rule."""
    
    def __init__(self, db_path: str = "freelancefeed.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS seen_jobs (
                    job_id TEXT,
                    platform TEXT NOT NULL,
                    chat_id INTEGER,
                    seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (job_id, chat_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    keywords TEXT DEFAULT '[]',
                    exclude_keywords TEXT DEFAULT '[]',
                    min_budget INTEGER DEFAULT 10,
                    digest_time TEXT DEFAULT '08:00',
                    timezone TEXT DEFAULT 'UTC',
                    enabled_platforms TEXT DEFAULT '{}',
                    is_paused BOOLEAN DEFAULT 0
                )
            """)
            conn.commit()
            
    def is_job_seen(self, job_id: str, chat_id: int) -> bool:
        """Check if a job has already been seen by a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM seen_jobs WHERE job_id = ? AND chat_id = ?", (job_id, chat_id))
            return cursor.fetchone() is not None
            
    def mark_job_seen(self, job_id: str, platform: str, chat_id: int):
        """Mark a job as seen for a specific user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO seen_jobs (job_id, platform, chat_id) VALUES (?, ?, ?)",
                    (job_id, platform, chat_id)
                )
                conn.commit()
        except sqlite3.IntegrityError:
            # Job is already marked as seen
            pass
            
    def cleanup_old_jobs(self, days: int = 30):
        """Remove jobs older than the specified number of days."""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM seen_jobs WHERE seen_at < ?",
                (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            if deleted_count > 0:
                logger.debug(f"Cleaned up {deleted_count} old jobs from database.")
                
    def get_seen_count(self, chat_id: int) -> int:
        """Get the total number of seen jobs currently in the database for a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM seen_jobs WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

    # User Management Methods
    def get_user_config(self, chat_id: int) -> dict:
        """Fetch or create user config using global env .env as defaults where applicable."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
                
            # Create new user based on global initial config
            global_conf = load_config()
            
            default_platforms = {
                "ENABLE_REMOTEOK": global_conf.get("ENABLE_REMOTEOK", True),
                "ENABLE_PEOPLEPERHOUR": global_conf.get("ENABLE_PEOPLEPERHOUR", True),
                "ENABLE_FREELANCER": global_conf.get("ENABLE_FREELANCER", True),
                "ENABLE_GURU": global_conf.get("ENABLE_GURU", True),
                "ENABLE_UPWORK": global_conf.get("ENABLE_UPWORK", True),
                "ENABLE_LINKEDIN": global_conf.get("ENABLE_LINKEDIN", True),
                "ENABLE_FIVERR": global_conf.get("ENABLE_FIVERR", False)
            }
            
            cursor.execute("""
                INSERT INTO users (chat_id, keywords, exclude_keywords, min_budget, digest_time, timezone, enabled_platforms, is_paused)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chat_id, 
                json.dumps(global_conf.get("KEYWORDS")), 
                json.dumps(global_conf.get("EXCLUDE_KEYWORDS")), 
                global_conf.get("MIN_BUDGET_USD"), 
                global_conf.get("DIGEST_TIME"), 
                global_conf.get("TIMEZONE"), 
                json.dumps(default_platforms),
                False
            ))
            conn.commit()
            
            cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
            return dict(cursor.fetchone())

    def update_user_setting(self, chat_id: int, column: str, value: typing.Any):
        """Update a specific column in the users table."""
        if column not in ["keywords", "exclude_keywords", "min_budget", "digest_time", "timezone", "enabled_platforms", "is_paused"]:
            raise ValueError(f"Invalid column name: {column}")
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {column} = ? WHERE chat_id = ?", (value, chat_id))
            conn.commit()
            
    def get_all_users(self):
        """Returns list of User configs for active scheduler routing."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE is_paused = 0")
            return [dict(row) for row in cursor.fetchall()]
