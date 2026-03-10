# FreelanceFeed by @duckb1t — duckb1t.cv
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import load_config
from database import Database
from scrapers import run_scrapers_for_user
import threading
from typing import Optional
import json
import pytz
import datetime
import time

logger = logging.getLogger(__name__)

PLATFORM_LABELS = {
    "ENABLE_REMOTEOK": "RemoteOK",
    "ENABLE_PEOPLEPERHOUR": "PeoplePerHour",
    "ENABLE_FREELANCER": "Freelancer.com",
    "ENABLE_GURU": "Guru",
    "ENABLE_UPWORK": "Upwork",
    "ENABLE_LINKEDIN": "LinkedIn",
    "ENABLE_FIVERR": "Fiverr",
}

class FeedBot:
    def __init__(self, config: dict):
        self.config = config
        self.db = Database()
        self.app = Application.builder().token(config["TELEGRAM_BOT_TOKEN"]).build()
        self._setup_handlers()

        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_scheduler = threading.Event()
        self.user_states: dict = {}  # chat_id -> state
        # job_cache[chat_id] = {"jobs": [...], "page": 0}
        self.job_cache: dict = {}

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("dashboard", self.cmd_dashboard))
        self.app.add_handler(CommandHandler("customizations", self.cmd_dashboard))
        self.app.add_handler(CommandHandler("run", self.cmd_run))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("cancel", self.cmd_cancel))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_input))


    # ─── Job Paginator ────────────────────────────────────────────────────────

    def _build_job_page(self, chat_id: int) -> tuple[str, InlineKeyboardMarkup]:
        """Builds a single-job page message with Prev/Next navigation buttons."""
        cache = self.job_cache.get(chat_id)
        if not cache or not cache["jobs"]:
            return "No jobs cached.", InlineKeyboardMarkup([])

        jobs = cache["jobs"]
        page = cache["page"]
        total = len(jobs)
        job = jobs[page]

        desc = (job.description or "").strip()
        if len(desc) > 280:
            desc = desc[:277] + "…"

        budget_str = f"💰 {job.budget}" if job.budget else "💰 Not specified"

        msg = (
            f"📋 *Job {page + 1} of {total}*\n"
            f"{'─' * 22}\n"
            f"🏷️ *{job.title}*\n"
            f"🌐 Platform: {job.platform}\n"
            f"{budget_str}\n"
            f"📅 {job.posted_at or 'Recently'}\n"
            f"{'─' * 22}\n"
            f"{desc}"
        )

        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data="job_prev"))
        nav_row.append(InlineKeyboardButton(f"· {page + 1}/{total} ·", callback_data="noop"))
        if page < total - 1:
            nav_row.append(InlineKeyboardButton("Next ▶️", callback_data="job_next"))

        keyboard = [
            nav_row,
            [InlineKeyboardButton("🔗 Open Job", url=job.url)],
            [InlineKeyboardButton("✅ Done", callback_data="job_done")],
        ]
        return msg, InlineKeyboardMarkup(keyboard)

    # ─── Dashboard Builder ────────────────────────────────────────────────────

    def _build_dashboard(self, user_config: dict) -> tuple[str, InlineKeyboardMarkup]:
        """Builds the dashboard message and its inline keyboard."""
        keywords = ", ".join(json.loads(user_config.get('keywords', '[]'))) or "None"
        excluded = ", ".join(json.loads(user_config.get('exclude_keywords', '[]'))) or "None"
        budget = user_config.get('min_budget', 0)
        digest_time = user_config.get('digest_time', '08:00')
        tz = user_config.get('timezone', 'UTC')
        is_paused = bool(user_config.get('is_paused'))

        platforms = json.loads(user_config.get('enabled_platforms', '{}'))
        active_count = sum(1 for v in platforms.values() if v)
        total_count = len(platforms)

        status_icon = "⏸️ Paused" if is_paused else "▶️ Active"
        pause_label = "▶️ Resume" if is_paused else "⏸️ Pause"

        msg = (
            "🛠️ *FreelanceFeed Dashboard*\n"
            "────────────────────\n"
            f"Status:    {status_icon}\n"
            f"Schedule:  {digest_time} ({tz})\n"
            f"Budget:    Min ${budget}\n"
            f"Keywords:  {keywords}\n"
            f"Excluded:  {excluded}\n"
            f"Platforms: {active_count}/{total_count} enabled\n"
            "────────────────────\n"
            "Tap a button below to edit:"
        )

        keyboard = [
            [InlineKeyboardButton(f"{pause_label} Daily Digest", callback_data="toggle_pause")],
            [
                InlineKeyboardButton("🔑 Keywords", callback_data="edit_keywords"),
                InlineKeyboardButton("🚫 Exclude", callback_data="edit_exclude"),
            ],
            [
                InlineKeyboardButton("💰 Budget", callback_data="edit_budget"),
                InlineKeyboardButton("⏰ Schedule", callback_data="edit_schedule"),
            ],
            [InlineKeyboardButton("🌍 Platforms", callback_data="show_platforms")],
            [InlineKeyboardButton("🔍 Scrape Now", callback_data="run_now")],
        ]
        return msg, InlineKeyboardMarkup(keyboard)

    def _build_platforms_keyboard(self, platforms: dict) -> InlineKeyboardMarkup:
        """Builds the platform toggle keyboard with live on/off state."""
        buttons = []
        for key, label in PLATFORM_LABELS.items():
            enabled = platforms.get(key, True)
            icon = "✅" if enabled else "❌"
            buttons.append([InlineKeyboardButton(f"{icon} {label}", callback_data=f"toggle_platform:{key}")])
        buttons.append([InlineKeyboardButton("⬅️ Back to Dashboard", callback_data="back_to_dashboard")])
        return InlineKeyboardMarkup(buttons)

    # ─── Job Sender ───────────────────────────────────────────────────────────

    async def _send_jobs(self, context, chat_id: int, user_config: Optional[dict] = None):
        if not chat_id:
            return
        if not user_config:
            user_config = self.db.get_user_config(chat_id)
        if user_config.get("is_paused"):
            return

        await context.bot.send_message(chat_id=chat_id, text="🔍 Scraping platforms for new jobs...")

        try:
            new_jobs = run_scrapers_for_user(user_config, self.db)
        except Exception as e:
            logger.error(f"Error during scraping for {chat_id}: {e}")
            await context.bot.send_message(chat_id=chat_id, text="⚠️ An error occurred while scraping.")
            return

        if not new_jobs:
            await context.bot.send_message(chat_id=chat_id, text="✅ All done! No new jobs found right now.")
            return

        # Cache and send paginated job browser
        self.job_cache[chat_id] = {"jobs": new_jobs, "page": 0}
        msg, markup = self._build_job_page(chat_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎯 Found *{len(new_jobs)} new jobs!* Browse below:",
            parse_mode='Markdown'
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode='Markdown',
            reply_markup=markup,
            disable_web_page_preview=True
        )

    # ─── Command Handlers ─────────────────────────────────────────────────────

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        first_name = update.effective_user.first_name or "there"
        self.db.get_user_config(chat_id)  # ensure row exists

        msg = (
            f"👋 *Hey {first_name}! I'm FreelanceFeed.*\n"
            "I scrape freelance jobs from 6+ platforms and deliver them straight to you.\n\n"
            "Here's what you can do:\n\n"
            "🛠️ /dashboard — View & customize all your settings\n"
            "🔍 /run — Scrape for new jobs right now\n"
            "📊 /status — See how many jobs you've tracked\n"
            "❓ /help — Full command reference\n\n"
            "Use /dashboard to set your keywords, budget, schedule, and timezone. "
            "Then I'll automatically send you a digest every day! 🚀"
        )
        keyboard = [
            [InlineKeyboardButton("🛠️ Open Dashboard", callback_data="open_dashboard")],
            [InlineKeyboardButton("🔍 Scrape Now", callback_data="run_now")],
        ]
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = (
            "❓ *FreelanceFeed Commands*\n"
            "────────────────────\n"
            "/start — Introduction & quick actions\n"
            "/dashboard — Your settings & customization panel\n"
            "/run — Scrape all platforms right now\n"
            "/status — Jobs tracked in your history\n"
            "/cancel — Cancel any active input prompt\n"
            "/help — Show this message\n"
            "────────────────────\n"
            "💡 *Tip:* Use `/dashboard` to change keywords, budget, timezone, and which platforms to scrape."
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def cmd_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_config = self.db.get_user_config(chat_id)
        msg, markup = self._build_dashboard(user_config)
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=markup)

    async def cmd_run(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_jobs(context, update.effective_chat.id)

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        count = self.db.get_seen_count(chat_id)
        user_config = self.db.get_user_config(chat_id)
        paused = "⏸️ Paused" if user_config.get('is_paused') else "▶️ Active"
        msg = (
            f"📊 *Your Stats*\n"
            f"────────────────────\n"
            f"Status:       {paused}\n"
            f"Jobs tracked: {count}\n"
            f"────────────────────\n"
            f"Open /dashboard to change settings."
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.user_states.pop(update.effective_chat.id, None)
        await update.message.reply_text("🛑 Cancelled. Use /dashboard to continue.")

    # ─── Callback Handler ─────────────────────────────────────────────────────

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        data = query.data
        user_config = self.db.get_user_config(chat_id)

        # ── Refresh dashboard inline after any action ──
        async def refresh_dashboard():
            user_config_fresh = self.db.get_user_config(chat_id)
            msg, markup = self._build_dashboard(user_config_fresh)
            try:
                await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=markup)
            except Exception:
                pass  # message might be unchanged

        if data == "open_dashboard" or data == "back_to_dashboard":
            await refresh_dashboard()

        elif data == "toggle_pause":
            new_val = not bool(user_config.get('is_paused'))
            self.db.update_user_setting(chat_id, "is_paused", int(new_val))
            await refresh_dashboard()

        elif data == "run_now":
            await query.edit_message_text("🔍 Starting scrape... check back in a moment!")
            await self._send_jobs(context, chat_id)

        elif data in ["edit_keywords", "edit_exclude", "edit_budget", "edit_schedule"]:
            self.user_states[chat_id] = data
            prompts = {
                "edit_keywords": (
                    "🔑 *Edit Include Keywords*\n\n"
                    "Send me a comma-separated list of keywords.\n"
                    "Jobs containing ANY of these will be sent to you.\n\n"
                    "Example: `python, django, automation, bot`\n\n"
                    "Or /cancel to go back."
                ),
                "edit_exclude": (
                    "🚫 *Edit Exclude Keywords*\n\n"
                    "Send me a comma-separated list of keywords to IGNORE.\n"
                    "Jobs matching these will be filtered out.\n\n"
                    "Example: `logo, design, data entry`\n\n"
                    "Or /cancel to go back."
                ),
                "edit_budget": (
                    "💰 *Edit Minimum Budget*\n\n"
                    "Send me a number in USD. Jobs below this budget will be skipped.\n\n"
                    "Example: `50`\n\n"
                    "Or /cancel to go back."
                ),
                "edit_schedule": (
                    "⏰ *Edit Daily Schedule & Timezone*\n\n"
                    "Send me the time and timezone in this format:\n"
                    "`HH:MM Timezone`\n\n"
                    "Examples:\n"
                    "`08:00 UTC`\n"
                    "`17:30 Asia/Dhaka`\n"
                    "`09:00 America/New_York`\n\n"
                    "Or /cancel to go back."
                ),
            }
            await query.edit_message_text(prompts[data], parse_mode='Markdown')

        elif data == "show_platforms":
            platforms = json.loads(user_config.get('enabled_platforms', '{}'))
            msg = "🌍 *Scraper Platforms*\n\nTap a platform to enable/disable it:"
            await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=self._build_platforms_keyboard(platforms))

        elif data.startswith("toggle_platform:"):
            key = data.split(":", 1)[1]
            platforms = json.loads(user_config.get('enabled_platforms', '{}'))
            if key in platforms:
                platforms[key] = not platforms[key]
                self.db.update_user_setting(chat_id, "enabled_platforms", json.dumps(platforms))
            # Refresh the platforms keyboard in-place
            user_config_fresh = self.db.get_user_config(chat_id)
            platforms_fresh = json.loads(user_config_fresh.get('enabled_platforms', '{}'))
            msg = "🌍 *Scraper Platforms*\n\nTap a platform to enable/disable it:"
            await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=self._build_platforms_keyboard(platforms_fresh))

        elif data == "noop":
            pass  # counter button, do nothing

        elif data == "job_next":
            cache = self.job_cache.get(chat_id)
            if cache and cache["page"] < len(cache["jobs"]) - 1:
                self.job_cache[chat_id]["page"] += 1
            msg, markup = self._build_job_page(chat_id)
            await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)

        elif data == "job_prev":
            cache = self.job_cache.get(chat_id)
            if cache and cache["page"] > 0:
                self.job_cache[chat_id]["page"] -= 1
            msg, markup = self._build_job_page(chat_id)
            await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)

        elif data == "job_done":
            self.job_cache.pop(chat_id, None)
            await query.edit_message_text(
                "✅ Done browsing. Use /run to scrape again or /dashboard to change your settings.",
            )

    # ─── Text Input Handler ─────────────────────────────────────────────────

    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        state = self.user_states.get(chat_id)
        if not state:
            return

        text = update.message.text.strip()

        try:
            if state == "edit_keywords":
                keys = [k.strip() for k in text.split(",") if k.strip()]
                self.db.update_user_setting(chat_id, "keywords", json.dumps(keys))
                await update.message.reply_text(f"✅ Keywords saved: `{', '.join(keys)}`\n\nUse /dashboard to view.", parse_mode='Markdown')

            elif state == "edit_exclude":
                keys = [k.strip() for k in text.split(",") if k.strip()]
                self.db.update_user_setting(chat_id, "exclude_keywords", json.dumps(keys))
                await update.message.reply_text(f"✅ Exclude keywords saved: `{', '.join(keys)}`\n\nUse /dashboard to view.", parse_mode='Markdown')

            elif state == "edit_budget":
                budget = int(text.replace('$', '').strip())
                if budget < 0:
                    raise ValueError("Budget must be a positive number.")
                self.db.update_user_setting(chat_id, "min_budget", budget)
                await update.message.reply_text(f"✅ Minimum budget set to *${budget}*.\n\nUse /dashboard to view.", parse_mode='Markdown')

            elif state == "edit_schedule":
                parts = text.split(maxsplit=1)
                time_str = parts[0]
                tz_str = parts[1].strip() if len(parts) > 1 else "UTC"

                datetime.datetime.strptime(time_str, "%H:%M")  # validate format
                pytz.timezone(tz_str)  # validate timezone

                self.db.update_user_setting(chat_id, "digest_time", time_str)
                self.db.update_user_setting(chat_id, "timezone", tz_str)
                await update.message.reply_text(
                    f"✅ Schedule set to *{time_str}* in *{tz_str}*.\n\nUse /dashboard to view.",
                    parse_mode='Markdown'
                )

        except (ValueError, Exception) as e:
            await update.message.reply_text(
                f"❌ Invalid input: `{e}`\n\nPlease try again or /cancel.",
                parse_mode='Markdown'
            )
            return  # keep state

        self.user_states.pop(chat_id, None)

    # ─── Scheduler ───────────────────────────────────────────────────────────

    def _run_for_user(self, chat_id: int):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from telegram import Bot
        bot = Bot(token=self.config["TELEGRAM_BOT_TOKEN"])

        class FakeContext:
            def __init__(self, b):
                self.bot = b

        loop.run_until_complete(self._send_jobs(FakeContext(bot), chat_id))
        loop.close()

    def _scheduler_loop(self):
        logger.info("Multi-user scheduler started. Polling every minute.")
        triggered = set()  # Track which (chat_id, HH:MM) already ran this minute

        while not self._stop_scheduler.is_set():
            now_utc = datetime.datetime.now(pytz.UTC)
            minute_key = now_utc.strftime("%Y-%m-%d %H:%M")

            for user in self.db.get_all_users():
                if user.get("is_paused"):
                    continue
                tz_str = user.get("timezone", "UTC")
                try:
                    user_tz = pytz.timezone(tz_str)
                except Exception:
                    user_tz = pytz.UTC

                now_local = now_utc.astimezone(user_tz)
                current_hhmm = now_local.strftime("%H:%M")
                target = user.get("digest_time", "08:00")
                run_key = (user['chat_id'], minute_key)

                if current_hhmm == target and run_key not in triggered:
                    triggered.add(run_key)
                    logger.info(f"Running digest for user {user['chat_id']}")
                    threading.Thread(target=self._run_for_user, args=(user['chat_id'],), daemon=True).start()

            # Clean old trigger keys
            if len(triggered) > 1000:
                triggered.clear()

            self.db.cleanup_old_jobs()

            for _ in range(60):
                if self._stop_scheduler.is_set():
                    break
                time.sleep(1)

    def start(self):
        logger.info("Starting FreelanceFeed bot...")
        t = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread = t
        t.start()
        self.app.run_polling()

    def stop(self):
        self._stop_scheduler.set()
