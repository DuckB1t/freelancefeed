# FreelanceFeed by @duckb1t — duckb1t.cv
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ConfigError(Exception):
    """Exception raised for errors in the configuration."""
    pass

def _get_bool_env(key: str, default: bool = True) -> bool:
    val = os.getenv(key, str(default)).lower()
    return val in ('true', '1', 't', 'y', 'yes')

def _get_list_env(key: str, default: str) -> list[str]:
    val = os.getenv(key, default)
    # Return empty list if string is empty, otherwise split and strip
    if not val.strip():
        return []
    return [item.strip().lower() for item in val.split(',')]

def load_config():
    """Validates and loads configuration from environment variables."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token or bot_token == "your_token_here":
        raise ConfigError(
            "TELEGRAM_BOT_TOKEN is missing or invalid. "
            "Please check your .env file and ensure it is set correctly."
        )

    config = {
        "TELEGRAM_BOT_TOKEN": bot_token,
        "KEYWORDS": _get_list_env("KEYWORDS", "python, wordpress, automation, bot, scraping"),
        "EXCLUDE_KEYWORDS": _get_list_env("EXCLUDE_KEYWORDS", "logo, design, video"),
        "MIN_BUDGET_USD": int(os.getenv("MIN_BUDGET_USD", "10")),
        "DIGEST_TIME": os.getenv("DIGEST_TIME", "08:00"),
        "TIMEZONE": os.getenv("TIMEZONE", "Asia/Dhaka"),
        
        # Scraper toggles
        "ENABLE_REMOTEOK": _get_bool_env("ENABLE_REMOTEOK"),
        "ENABLE_PEOPLEPERHOUR": _get_bool_env("ENABLE_PEOPLEPERHOUR"),
        "ENABLE_FREELANCER": _get_bool_env("ENABLE_FREELANCER"),
        "ENABLE_GURU": _get_bool_env("ENABLE_GURU"),
        "ENABLE_UPWORK": _get_bool_env("ENABLE_UPWORK"),
        "ENABLE_LINKEDIN": _get_bool_env("ENABLE_LINKEDIN"),
        "ENABLE_FIVERR": _get_bool_env("ENABLE_FIVERR"),
    }
    
    return config

if __name__ == "__main__":
    try:
        conf = load_config()
        print("Configuration loaded successfully:")
        for k, v in conf.items():
            if k == "TELEGRAM_BOT_TOKEN":
                print(f"  {k}: {'*' * len(v)}") # Mask token for safety
            else:
                print(f"  {k}: {v}")
    except ConfigError as e:
        print(f"Configuration Error: {e}")
