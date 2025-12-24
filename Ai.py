#!/usr/bin/env python3
"""
Xiaomi MiMo AI Telegram Bot
Built on official MiMo API behavior
"""

import os
import sys
import json
import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime

import aiohttp
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ====================== Logging ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("mimo_bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("MiMoBot")

# ====================== Config ======================
class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    MIMO_API_KEY = os.getenv("MIMO_API_KEY")

    # ✅ Official endpoint + model
    MIMO_API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
    MIMO_MODEL = "mimo-v2-flash"

    PORT = int(os.getenv("PORT", 8080))
    PUBLIC_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")

    TIMEOUT = 30
    MAX_INPUT = 2000
    MAX_HISTORY = 8

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN or not cls.MIMO_API_KEY:
            logger.error("❌ Missing TELEGRAM_TOKEN or MIMO_API_KEY")
            return False
        return True

# ====================== Memory ======================
memory: dict[int, deque] = defaultdict(
    lambda: deque(maxlen=Config.MAX_HISTORY)
)

# ====================== Utils ======================
def split_message(text: str, limit=4000):
    parts = []
    while len(text) > limit:
        cut = text[:limit].rfind("\n")
        cut = cut if cut != -1 else limit
        parts.append(text[:cut])
        text = text[cut:].strip()
    parts.append(text)
    return parts

# ====================== MiMo API ======================
async def call_mimo_ai(user_id: int, prompt: str) -> str:
    headers = {
        "api-key": Config.MIMO_API_KEY,   # ✅ correct header
        "Content-Type": "application/json"
    }

    messages = list(memory[user_id])
    messages.append({
        "role": "user",
        "content": prompt
    })

    payload = {
        "model": Config.MIMO_MODEL,
        "messages": messages
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                Config.MIMO_API_URL,
                headers=headers,
                json=payload,
                timeout=Config.TIMEOUT
            ) as resp:

                raw = await resp.text()
                logger.info(f"MiMo [{resp.status}] {raw[:200]}")

                if resp.status != 200:
                    return f"❌ MiMo API Error ({resp.status})"

                data = json.loads(raw)

                reply = data["choices"][0]["message"]["content"]

                # store assistant reply
                memory[user_id].append({
                    "role": "assistant",
                    "content": reply
                })

                return reply.strip()

    except asyncio.TimeoutError:
        return "⏰ انتهت مهلة الاتصال"
    except aiohttp.ClientError:
        return "🌐 خطأ في الاتصال بالخادم"
    except Exception as e:
        logger.error(e, exc_info=True)
        return "❌ خطأ داخلي"

# ====================== Commands ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Xiaomi MiMo AI Bot**\n\n"
        "أرسل أي رسالة وسأرد عليك باستخدام MiMo.\n\n"
        "/status – حالة النظام\n"
        "/reset – تصفير المحادثة",
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        f"📊 **Status**\n\n"
        f"🕒 {datetime.now()}\n"
        f"🧠 Model: `{Config.MIMO_MODEL}`\n"
        f"💬 Memory: {len(memory[uid])}",
        parse_mode="Markdown"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    memory[update.effective_user.id].clear()
    await update.message.reply_text("♻️ تم تصفير المحادثة")

# ====================== Messages ======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if len(text) > Config.MAX_INPUT:
        await update.message.reply_text("📏 الرسالة طويلة جداً")
        return

    wait = await update.message.reply_text("🤔 جاري التفكير...")

    reply = await call_mimo_ai(user.id, text)

    try:
        await wait.delete()
    except:
        pass

    for part in split_message(reply):
        await update.message.reply_text(part)

# ====================== Error ======================
async def error_handler(update, context):
    logger.error(context.error, exc_info=True)
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ حدث خطأ تقني")

# ====================== Main ======================
def main():
    if not Config.validate():
        sys.exit(1)

    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    async def setup(app):
        await app.bot.set_my_commands([
            BotCommand("start", "بدء"),
            BotCommand("status", "حالة النظام"),
            BotCommand("reset", "تصفير المحادثة"),
        ])

    app.post_init = setup

    if Config.PUBLIC_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=Config.PORT,
            webhook_url=f"https://{Config.PUBLIC_URL}"
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
