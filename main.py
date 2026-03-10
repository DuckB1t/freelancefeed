# FreelanceFeed by @duckb1t — duckb1t.cv
import sys
import argparse
import logging
import json
from config import load_config, ConfigError
from bot import FeedBot
from database import Database
from scrapers import run_scrapers_for_user
import asyncio
from telegram import Bot

# Set up logging to show INFO to stdout
logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)

def print_banner():
    print("╔══════════════════════════════════╗")
    print("║  FreelanceFeed                   ║")
    print("║  by @duckb1t • duckb1t.cv        ║")
    print("╚══════════════════════════════════╝")
    print()

def start_bot(config):
    async def verify_and_start():
        bot = Bot(token=config["TELEGRAM_BOT_TOKEN"])
        try:
            me = await bot.get_me()
            print(f"Connected as: @{me.username}")
            print(f"Scheduler: Daily digests active")
            print(f"Listening for commands... (Ctrl+C to stop)\n")
        except Exception as e:
            print(f"❌ Telegram connection failed: {e}")
            sys.exit(1)

    print("Connecting to Telegram...")
    asyncio.run(verify_and_start())

    feed_bot = FeedBot(config)
    try:
        feed_bot.start() # This blocks
    except KeyboardInterrupt:
        print("\nStopping bot...")
        feed_bot.stop()

def run_scrapers_now(config):
    print("Running scrapers right now (CLI mapping to default settings)...")
    db = Database()
    
    # In CLI mode, we just pass down the global config mapped to a dummy user dict
    # so the new multi-user structure doesn't crash.
    default_platforms = {
        "ENABLE_REMOTEOK": config.get("ENABLE_REMOTEOK", True),
        "ENABLE_PEOPLEPERHOUR": config.get("ENABLE_PEOPLEPERHOUR", True),
        "ENABLE_FREELANCER": config.get("ENABLE_FREELANCER", True),
        "ENABLE_GURU": config.get("ENABLE_GURU", True),
        "ENABLE_UPWORK": config.get("ENABLE_UPWORK", True),
        "ENABLE_LINKEDIN": config.get("ENABLE_LINKEDIN", True),
        "ENABLE_FIVERR": config.get("ENABLE_FIVERR", False)
    }
    
    dummy_user_config = {
        "chat_id": 0, # CLI user
        "keywords": json.dumps(config.get("KEYWORDS")),
        "exclude_keywords": json.dumps(config.get("EXCLUDE_KEYWORDS")),
        "min_budget": config.get("MIN_BUDGET_USD"),
        "enabled_platforms": json.dumps(default_platforms)
    }
    
    new_jobs = run_scrapers_for_user(dummy_user_config, db)
    
    if new_jobs:
        print(f"\nFound {len(new_jobs)} new jobs matching your criteria!")
        for i, job in enumerate(new_jobs, 1):
            print(f"\n--- Job {i} ---")
            print(f"[{job.platform.upper()}] {job.title}")
            print(f"Budget: {job.budget or 'N/A'}")
            print(f"URL: {job.url}")
    else:
        print("\nNo new jobs found matching your criteria.")

def test_connection(config):
    print("Testing Telegram connection...")
    async def try_connect():
        bot = Bot(token=config["TELEGRAM_BOT_TOKEN"])
        try:
            me = await bot.get_me()
            print(f"✅ Successfully connected to Telegram as {me.first_name} (@{me.username})")
        except Exception as e:
            print(f"❌ Failed to connect to Telegram. Error:\n{e}")
            
    asyncio.run(try_connect())

def show_config(config):
    print("Current Configuration:")
    for k, v in config.items():
        if k == "TELEGRAM_BOT_TOKEN":
            # Mask the token
            visible_chars = min(4, len(v) // 2)
            masked_token = v[:visible_chars] + "*" * (len(v) - visible_chars*2) + v[-visible_chars:] if len(v) > 8 else "***"
            print(f"  {k}: {masked_token}")
        else:
            print(f"  {k}: {v}")

def main():
    parser = argparse.ArgumentParser(description="FreelanceFeed - Never miss a freelance job again.")
    parser.add_argument("command", nargs="?", default="start", choices=["start", "run", "test", "config"], help="The command to execute (defaults to 'start')")
    
    args = parser.parse_args()
    
    print_banner()
    
    try:
        config = load_config()
    except ConfigError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    if args.command == "start":
        start_bot(config)
    elif args.command == "run":
        run_scrapers_now(config)
    elif args.command == "test":
        test_connection(config)
    elif args.command == "config":
        show_config(config)

if __name__ == "__main__":
    main()
