#!/usr/bin/env python3
"""
Mimo AI Telegram Bot
FINAL WORKING VERSION
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from collections import defaultdict, deque

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
logger = logging.getLogger("MimoBot")

# ====================== Config ======================
class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    MIMO_API_KEY = os.getenv("MIMO_AI_API_KEY")
    MIMO_API_URL = os.getenv("MIMO_AI_API_URL")

    # ✅ model مطلوب إجباري
    MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-chat")

    PORT = int(os.getenv("PORT", 8080))
    PUBLIC_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")

    TIMEOUT = 30
    MAX_INPUT = 2000
    MAX_HISTORY = 6

    @classmethod
    def validate(cls):
        missing = []
        if not cls.TELEGRAM_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.MIMO_API_KEY:
            missing.append("MIMO_AI_API_KEY")
        if not cls.MIMO_API_URL:
            missing.append("MIMO_AI_API_URL")

        if missing:
            logger.error(f"❌ Missing env vars: {', '.join(missing)}")
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

# ====================== Mimo AI Client ======================
async def call_mimo_ai(user_id: int, prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {Config.MIMO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "model": Config.MIMO_MODEL,   # ✅ الحل هنا
        "prompt": prompt,
        "max_tokens": 800,
        "temperature": 0.7
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
                logger.info(f"MIMO RAW [{resp.status}]: {raw[:300]}")

                if resp.status != 200:
                    return (
                        f"❌ Mimo API Error\n"
                        f"Status: {resp.status}\n"
                        f"Response:\n{raw[:500]}"
                    )

                data = json.loads(raw)

                reply = (
                    data.get("response")
                    or data.get("result")
                    or data.get("text")
                    or data.get("choices", [{}])[0].get("text")
                )

                if not reply:
                    return f"⚠️ API Response:\n{json.dumps(data, ensure_ascii=False, indent=2)[:800]}"

                return reply.strip()

    except asyncio.TimeoutError:
        return "⏰ انتهت مهلة الاتصال مع Mimo"
    except aiohttp.ClientError as e:
        logger.error(e)
        return "🌐 فشل الاتصال بالخادم"
    except Exception as e:
        logger.error(e, exc_info=True)
        return "❌ خطأ داخلي غير متوقع"

# ====================== Commands ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Mimo AI Bot**\n\n"
        "جاهز للعمل الآن ✅\n\n"
        "📌 أوامر:\n"
        "/status – حالة النظام\n"
        "/test – اختبار الاتصال\n"
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

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🧪 اختبار الاتصال مع Mimo...")
    result = await call_mimo_ai(update.effective_user.id, "مرحبا، هل تعمل؟")
    await msg.edit_text(f"🧪 النتيجة:\n\n{result}")

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
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    async def setup(app):
        await app.bot.set_my_commands([
            BotCommand("start", "بدء"),
            BotCommand("status", "حالة النظام"),
            BotCommand("test", "اختبار الاتصال"),
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
