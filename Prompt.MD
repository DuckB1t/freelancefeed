# FreelanceFeed — What I Want To Build

---

## The Idea

I want a Telegram bot that scrapes freelance job listings from all
major platforms and sends them to me every day automatically.

The problem I'm solving: I have to open 7 different websites every
day just to check for new jobs. I want the bot to do that for me
and just ping me on Telegram with whatever is new and relevant.

The bot is a personal tool. Just for me. One person. No sign up,
no dashboard, no SaaS nonsense.

---

## How It Works — Plain English

I run the bot on my machine or a VPS. (or planform like katabump) It wakes up every morning
at a time I set, goes and scrapes all the freelance platforms,
filters the jobs by keywords I care about, throws away any jobs
it already sent me before, and sends whatever's left to my Telegram.

That's it. Simple.

I can also message the bot manually anytime to trigger a scrape
right now without waiting for the scheduled time.

---

## The Platforms It Scrapes

- RemoteOK
- PeoplePerHour
- Freelancer.com
- Guru
- Upwork
- LinkedIn Jobs
- Fiverr (if possible without login, otherwise skip for now)

---

## The Filtering

I set my keywords in a config file. Like "python, wordpress,
automation, bot, scraping". The bot only sends me jobs that
mention at least one of my keywords in the title or description.

I can also set keywords to exclude. Like "logo, design, video" —
so I never see those jobs.

I can set a minimum budget too. If a job pays less than $10 I
don't want to see it.

---

## The Telegram Experience

When the bot has new jobs for me, it sends them like this:

---
[PLATFORM] // NEW JOB

Title of the job here
Short preview of the description, maybe 200 characters max...

Budget  : $50-$200
Tags    : python, automation
Posted  : 2 hours ago

Apply → link to the job
──────────────────
FreelanceFeed by @duckb1t • duckb1t.cv
---

Max 5 jobs per message so it doesn't spam me. If there are more
than 5 new jobs it just sends another message after.

No emojis anywhere in the messages. Clean plain text only.

The credit line at the bottom always stays. Never remove it.

---

## Bot Commands

When I message the bot:

/start — bot says hi, tells me it's running, shows my current
         keyword config, and tells me when the next digest is

/run   — run the scrapers right now, don't wait for the schedule

/status — tell me when the last run was and how many jobs were found

/pause — stop the scheduled runs temporarily

/resume — start the scheduled runs again

/help — show all commands

---

## The "Never Show Me The Same Job Twice" Part

The bot keeps a record of every job it already sent me. If it
scrapes a job it already sent before, it skips it silently.
This record auto-cleans itself after 30 days so old jobs can
show up fresh again if they're reposted.

---

## Config

I set everything in a simple .env file:
- My Telegram bot token (from @BotFather)
- My keywords
- My excluded keywords
- My minimum budget
- Which platforms to turn on or off
- What time to run the daily digest
- My timezone (Asia/Dhaka)

The bot token is the only required thing. Everything else has
sensible defaults.

---

## CLI

I run it from the terminal. Commands:

python main.py start   — starts the bot and scheduler
python main.py run     — scrape right now, once
python main.py test    — check that Telegram is connected
python main.py config  — show me my current settings

When it runs, the terminal shows a banner:

╔══════════════════════════════════╗
║  FreelanceFeed                   ║
║  by @duckb1t • duckb1t.cv        ║
╚══════════════════════════════════╝

Then shows a live progress bar of which platforms are being scraped.

---

## When Something Breaks

If one platform fails to scrape, that's fine — just skip it and
continue with the others. Don't crash everything because LinkedIn
was being annoying.

If a platform fails 3 times in a row across different runs, send
me a Telegram message saying "hey PPH keeps failing, disabled it."

---

## Credits — Baked Into Everything

Every single Python file starts with:
# FreelanceFeed by @duckb1t — duckb1t.cv

The bot startup message shows my name and link.
Every Telegram message has my credit line at the bottom.
The CLI banner shows my name.
The README has my name at the top and bottom.

---

## The README

Write the README last, after everything is working.

It should be the best README anyone has seen for a tool like this.
No emojis anywhere. Use SVG badges from shields.io for everything.
Badges: Python version, MIT license, number of platforms, Telegram,
GitHub stars, last commit.

Sections to include:
1. Project name + tagline + author credit + badges
2. What this is and what problem it solves (short, 3-4 sentences)
3. Feature list (use -> instead of bullet emojis)
4. Supported platforms table (platform, method, status, needs login)
5. Quick start (4 steps max, copy-paste ready)
6. Config reference table (every .env variable explained)
7. How to get a Telegram bot token (step by step, no fluff)
8. CLI commands table
9. Self-hosting (cron one-liner + Docker option)
10. How it works (ASCII flow diagram)
11. Project file structure with descriptions
12. Known limitations (be honest)
13. Contributing guide
14. Footer with my name and links

---

## Commit Style

Conventional commits. No emojis. Ever.

feat: what was added
fix: what was fixed
docs: readme/docs changes
refactor: code restructure
chore: boring maintenance stuff

---

## What To Name It

Project name: FreelanceFeed
GitHub repo: freelancefeed
Tagline: Never miss a freelance job again.

---

## Start Building

Start with the config loader and the basic project folder structure.
Show me those files first. Nothing else yet.