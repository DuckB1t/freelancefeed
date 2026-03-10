# FreelanceFeed
### Never miss a freelance job again.
#### Developed by [@duckb1t](https://duckb1t.cv)

![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Platforms](https://img.shields.io/badge/platforms-7-orange?style=flat-square)
![Telegram](https://img.shields.io/badge/telegram-active-blue?logo=telegram&style=flat-square)
![Stars](https://img.shields.io/github/stars/duckb1t/freelancefeed?style=flat-square)
![Last Commit](https://img.shields.io/github/last-commit/duckb1t/freelancefeed?style=flat-square)

FreelanceFeed is a professional-grade Telegram bot designed to aggregate, filter, and deliver high-quality freelance job listings directly to your chat. By automating the monitoring of multiple job boards, it eliminates the need for manual daily searches across fragmented platforms. The bot ensures you only see relevant opportunities by applying personalized keyword and budget filters.

## Features
-> Interactive Customization Dashboard: Manage all settings via a Telegram-based GUI.
-> Multi-Platform Scraper Engine: Supports 7 major freelance and remote job platforms.
-> Smart Deduplication: Guaranteed unique results — never see the same job twice.
-> Granular Filtering: Advanced keyword inclusion, exclusion, and minimum budget thresholds.
-> Automated Digests: Personalized delivery schedules based on your specific timezone.
-> Paginated Job Browser: Navigate through search results with intuitive Previous and Next controls.

## Supported Platforms
| Platform | Method | Status | Needs Login |
| :--- | :--- | :--- | :--- |
| RemoteOK | API JSON | Working | No |
| PeoplePerHour | HTML Parsing | Working | No |
| Freelancer.com | RSS XML | Working | No |
| LinkedIn | HTML Parsing | Working | No |
| Upwork | RSS XML | Deprecated RSS | Yes |
| Guru | RSS XML | Removed | No |
| Fiverr | N/A | Skipped | Yes |

## Quick Start
1. Clone the repository: `git clone https://github.com/duckb1t/freelancefeed.git && cd freelancefeed`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment: `cp .env.example .env` and insert your `TELEGRAM_BOT_TOKEN`.
4. Launch application: `python main.py start` then send `/start` to your bot.

## Config Reference (.env)
| Variable | Description |
| :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Your unique bot token obtained from @BotFather. |
| `KEYWORDS` | Target job keywords (comma-separated). |
| `EXCLUDE_KEYWORDS` | Keywords to ignore (comma-separated). |
| `MIN_BUDGET_USD` | The minimum budget required to trigger an alert. |
| `DIGEST_TIME` | Scheduled delivery time for daily updates (HH:MM). |
| `TIMEZONE` | Your local timezone (e.g., Asia/Dhaka). |
| `ENABLE_PLATFORM` | Boolean toggles for individual scrapers. |

## How to get a Telegram Bot Token
1. Open the Telegram application and search for @BotFather.
2. Execute the `/newbot` command.
3. Follow the prompts to assign a name and a username to your bot.
4. Securely copy the API token provided in the response.
5. Paste this token into your `.env` file under `TELEGRAM_BOT_TOKEN`.

## CLI Commands
| Command | Action |
| :--- | :--- |
| `python main.py start` | Initiates the bot daemon and the automated scheduler. |
| `python main.py run` | Triggers an immediate scrape and outputs results to terminal. |
| `python main.py test` | Validates the integrity of the Telegram API connection. |
| `python main.py config` | Displays the current running configuration (token masked). |

## Self-Hosting
### Cron Execution
For environments where a persistent daemon is not preferred, use a cron job to trigger the scraper:
```bash
0 8 * * * cd /path/to/freelancefeed && /path/to/venv/bin/python main.py run > /dev/null 2>&1
```

### Docker
A Dockerfile is included for containerized deployments. Build and run with:
```bash
docker build -t freelancefeed .
docker run -d --env-file .env freelancefeed
```

## How It Works
```text
[Multi-User Bot] --> (Stores persistent configuration in SQLite)
       |
[Background Scheduler] --> (Checks for due digests every minute)
       |
[Scraper Engine] --> (Executes per-user platform requests)
       |
[Filter Engine] 
   1. Seen Filter: Has the specific user already cached this ID?
   2. Keyword Match: Does the job contain target inclusion keywords?
   3. Exclude Filter: Does the job contains forbidden keywords?
   4. Budget Check: Does the budget meet the user requirement?
       |
[Pagination Browser] --> (Interactive Telegram UI for result delivery)
```

## Project Structure
```text
freelancefeed/
├── scrapers/          # Modular scraping implementations
│   ├── base.py        # Abstract base class for scrapers
│   └── ...            # Platform-specific implementations
├── bot.py             # Telegram interface and scheduler logic
├── config.py          # Environment and configuration manager
├── database.py        # Persistence layer for users and job history
├── main.py            # CLI entrypoint and bootstrap
├── models.py          # Core job data models and filtering logic
└── requirements.txt   # Application dependencies
```

## Known Limitations
-> Platforms frequently update their HTML structures, which may intermittently break specific scrapers.
-> RSS feeds for platforms like Upwork and Guru have been deprecated or restricted.
-> LinkedIn scraping is restricted to public listings and may be subject to rate limiting.

## Contributing
Contributions to maintain scraping regexes and HTML selectors are welcome. Please ensure all code adheres to the project's logging standards and avoids the use of emojis within the codebase.

---
<p align="center">FreelanceFeed by <a href="https://duckb1t.cv">@duckb1t</a></p>
