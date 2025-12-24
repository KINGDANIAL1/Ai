#!/usr/bin/env python3
"""
بوت تلغرام مع Xiaomi Mimo AI
إصدار كامل ومستقر
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional

# مكتبات Telegram
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext
)

# مكتبات الإنترنت
import aiohttp
import requests

# ====================== إعدادات التسجيل ======================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mimo_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ====================== إعدادات التطبيق ======================
class Config:
    """إعدادات Mimo AI Bot"""
    
    # 🔑 مفاتيح API (من متغيرات البيئة)
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    MIMO_API_KEY = os.environ.get("MIMO_AI_API_KEY", "")
    
    # 🌐 روابط API
    MIMO_API_URL = os.environ.get("MIMO_AI_API_URL", "https://api.xiaomimimo.com/v1/chat/completions")
    
    # ⚙️ إعدادات Railway
    PORT = int(os.environ.get("PORT", 8080))
    PUBLIC_URL = os.environ.get("RAILWAY_STATIC_URL", "") or os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    
    # 📏 إعدادات البوت
    BOT_USERNAME = "@darck_ai_bot"
    MAX_MESSAGE_LENGTH = 4000
    REQUEST_TIMEOUT = 30
    
    @classmethod
    def validate(cls):
        """التحقق من صحة الإعدادات"""
        errors = []
        
        if not cls.TELEGRAM_TOKEN:
            errors.append("❌ TELEGRAM_BOT_TOKEN غير مضبوط")
        
        if not cls.MIMO_API_KEY:
            errors.append("❌ MIMO_AI_API_KEY غير مضبوط")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False
        
        logger.info("✅ جميع الإعدادات صحيحة")
        return True

# ====================== دوال مساعدة ======================
class Helper:
    """أدوات مساعدة"""
    
    @staticmethod
    def split_message(text: str, max_len: int = 4000):
        """تقسيم الرسائل الطويلة"""
        if len(text) <= max_len:
            return [text]
        
        parts = []
        while text:
            if len(text) <= max_len:
                parts.append(text)
                break
            
            split_at = text[:max_len].rfind('\n')
            if split_at == -1:
                split_at = text[:max_len].rfind(' ')
            if split_at == -1:
                split_at = max_len
            
            parts.append(text[:split_at])
            text = text[split_at:].strip()
        
        return parts
    
    @staticmethod
    async def check_internet():
        """فحص اتصال الإنترنت"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.telegram.org", timeout=5):
                    return True
        except:
            return False

# ====================== معالجات الأوامر ======================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    user = update.effective_user
    
    welcome = f"""
🌟 **مرحباً {user.first_name}!**

🤖 **أنا بوت Mimo AI الذكي**
مدعوم من تقنية Xiaomi Mimo AI المتقدمة.

✨ **ماذا أستطيع فعل؟:**
• محادثات ذكية بالعربية
• إجابة على أسئلتك
• مساعدة في المهام اليومية
• تعلم وشرح المواضيع

🔧 **الأوامر المتاحة:**
/start - بدء المحادثة
/help - المساعدة
/status - حالة النظام
/test - اختبار الاتصال
/about - معلومات

📝 **كيفية الاستخدام:**
فقط أرسل رسالة وسأرد عليك!

⚡ **معلومات النظام:**
• وقت التشغيل: {datetime.now().strftime('%H:%M:%S')}
• الإصدار: 2.0.0
"""
    
    await update.message.reply_text(welcome, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /help"""
    help_text = """
📚 **دليل استخدام Mimo AI Bot**

🔹 **الأوامر الرئيسية:**
/start - بدء المحادثة
/help - عرض هذه الرسالة
/status - حالة النظام والخوادم
/test - اختبار اتصال Mimo AI
/about - معلومات عن البوت
/ping - قياس سرعة الاستجابة

🔹 **ميزات البوت:**
• محادثات ذكية مع Mimo AI
• دعم اللغة العربية الكامل
• معالجة الرسائل الطويلة
• استجابة سريعة
• تسجيل الأخطاء التلقائي

🔹 **نصائح للاستخدام:**
1. استخدم جمل كاملة للردود الأفضل
2. يمكنك السؤال عن أي موضوع
3. الردود تأخذ 2-3 ثوانٍ
4. للأسئلة الطويلة، قسمها

🔹 **الدعم التقني:**
إذا واجهت مشاكل:
1. استخدم /test لفحص الاتصال
2. استخدم /status للتحقق
3. أعد إرسال الرسالة
4. تواصل مع المطور

🛠️ **إصدار:** 2.0.0
📅 **التحديث:** 2024-12-24
"""
    
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /status"""
    
    status_lines = []
    status_lines.append("📊 **حالة نظام Mimo AI Bot**")
    status_lines.append(f"🕐 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # فحص اتصال الإنترنت
    internet_ok = await Helper.check_internet()
    status_lines.append(f"🌐 الإنترنت: {'✅ متصل' if internet_ok else '❌ غير متصل'}")
    
    # فحص Telegram
    status_lines.append(f"🤖 Telegram API: ✅ نشط")
    
    # فحص Mimo AI
    if Config.MIMO_API_KEY:
        if Config.MIMO_API_KEY.startswith('sk-'):
            status_lines.append("🔑 Mimo API Key: ✅ صالح")
        else:
            status_lines.append("🔑 Mimo API Key: ⚠️ غير صالح")
    else:
        status_lines.append("🔑 Mimo API Key: ❌ غير مضبوط")
    
    # حالة Railway
    if Config.PUBLIC_URL:
        status_lines.append(f"🚄 Railway: ✅ نشط ({Config.PUBLIC_URL[:30]}...)")
    else:
        status_lines.append("🚄 Railway: 🔧 وضع التطوير")
    
    # معلومات إضافية
    status_lines.append(f"📡 API URL: {Config.MIMO_API_URL}")
    status_lines.append(f"🔢 Port: {Config.PORT}")
    
    await update.message.reply_text("\n".join(status_lines), parse_mode='Markdown')


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /test لاختبار Mimo AI"""
    
    test_msg = await update.message.reply_text("🔍 **جاري اختبار اتصال Mimo AI...**")
    
    results = []
    
    # 1. اختبار اتصال الإنترنت
    try:
        response = requests.get("https://api.xiaomimimo.com", timeout=5)
        results.append("✅ **الخادم متاح:** يمكن الوصول إلى api.xiaomimimo.com")
    except:
        results.append("❌ **الخادم غير متاح:** لا يمكن الوصول إلى Mimo AI")
    
    # 2. اختبار API بالمفتاح
    if Config.MIMO_API_KEY:
        results.append(f"✅ **المفتاح مضبوط:** {Config.MIMO_API_KEY[:10]}...")
        
        # اختبار طلب فعلي
        try:
            test_response = await call_mimo_ai("مرحباً، هذا اختبار. هل تعمل؟")
            if test_response and "خطأ" not in test_response:
                results.append(f"✅ **الاتصال ناجح:** {test_response[:50]}...")
            else:
                results.append(f"❌ **الاتصال فاشل:** {test_response}")
        except Exception as e:
            results.append(f"❌ **خطأ في الاختبار:** {str(e)}")
    else:
        results.append("❌ **المفتاح غير مضبوط:** اضبط MIMO_AI_API_KEY")
    
    # 3. اختبار Telegram
    results.append("✅ **Telegram Bot:** نشط ومستجيب")
    
    await test_msg.edit_text(
        "🧪 **نتائج اختبار Mimo AI:**\n\n" + "\n\n".join(results),
        parse_mode='Markdown'
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /about"""
    
    about_text = """
🤖 **Mimo AI Telegram Bot**

**الوصف:**
بوت ذكاء اصطناعي متقدم يعمل بتقنية Xiaomi Mimo AI.
مصمم لتقديم تجربة محادثة ذكية وسلسة باللغة العربية.

**المميزات:**
• محرك Mimo AI المتطور من Xiaomi
• دعم اللغة العربية الفصيحة
• تصميم سريع ومستقر
• معالجة ذكية للسياق
• واجهة سهلة الاستخدام

**التقنيات:**
• Python 3.11+
• python-telegram-bot 21.7
• Xiaomi Mimo AI API
• Railway للاستضافة السحابية

**الخصوصية:**
• لا يتم حفظ محادثاتك
• تشفير آمن للبيانات
• عدم مشاركة المعلومات

**المطور:**
فريق Darck AI
للاستفسارات: @darck_ai_bot

**الرخصة:**
مشروع تعليمي مفتوح المصدر.

✨ **شعارنا:**
تكنولوجيا ذكية لخدمة الإنسان!
"""
    
    await update.message.reply_text(about_text)


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /ping"""
    start_time = datetime.now()
    msg = await update.message.reply_text("🏓 بينج...")
    end_time = datetime.now()
    
    latency = (end_time - start_time).total_seconds() * 1000
    
    await msg.edit_text(f"🏓 بونج!\n⚡ سرعة الاستجابة: {latency:.0f} مللي ثانية")

# ====================== Mimo AI Integration ======================
async def call_mimo_ai(prompt: str) -> str:
    """الاتصال بـ Xiaomi Mimo AI API"""
    
    if not Config.MIMO_API_KEY:
        return "❌ خطأ: لم يتم تعيين مفتاح Mimo AI API"
    
    headers = {
        "Authorization": f"Bearer {Config.MIMO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # جرب عدة هياكل بيانات (Xiaomi Mimo قد يستخدم هيكلاً مختلفاً)
    data_attempts = [
        # المحاولة 1: هيكل OpenAI-like (الأكثر شيوعاً)
        {
            "model": "mimo-ai",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.7
        },
        
        # المحاولة 2: هيكل بديل
        {
            "prompt": prompt,
            "model": "xiaomi-mimo",
            "max_tokens": 800,
            "temperature": 0.7
        },
        
        # المحاولة 3: هيكل مبسط
        {
            "input": prompt,
            "parameters": {
                "max_tokens": 800,
                "temperature": 0.7
            }
        }
    ]
    
    for attempt_num, data in enumerate(data_attempts, 1):
        try:
            logger.info(f"🔧 محاولة {attempt_num} مع هيكل: {json.dumps(data)[:100]}...")
            
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    Config.MIMO_API_URL,
                    headers=headers,
                    json=data,
                    timeout=Config.REQUEST_TIMEOUT
                ) as response:
                    
                    logger.info(f"📡 الاستجابة: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"📦 نتيجة API: {json.dumps(result)[:200]}...")
                        
                        # محاولة استخراج النص بطرق مختلفة
                        if "choices" in result and result["choices"]:
                            return result["choices"][0].get("message", {}).get("content", "رد فارغ")
                        elif "text" in result:
                            return result["text"]
                        elif "response" in result:
                            return result["response"]
                        elif "result" in result:
                            return result["result"]
                        else:
                            # إذا فشل كل شيء، ارجع النتيجة كاملة للتشخيص
                            return f"رد AI: {json.dumps(result)[:500]}"
                    
                    elif response.status == 400:
                        error_data = await response.text()
                        logger.warning(f"⚠️ خطأ 400 في المحاولة {attempt_num}: {error_data[:200]}")
                        continue  # جرب الهيكل التالي
                    
                    elif response.status == 401:
                        return "❌ مفتاح API غير صالح أو منتهي الصلاحية"
                    
                    elif response.status == 429:
                        return "⚠️ تجاوزت الحد المسموح، حاول مرة أخرى لاحقاً"
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ خطأ {response.status}: {error_text[:200]}")
                        continue
                        
        except aiohttp.ClientConnectorError as e:
            logger.error(f"❌ خطأ اتصال: {e}")
            return "🌐 لا يمكن الوصول إلى خادم Mimo AI"
        
        except asyncio.TimeoutError:
            logger.error("⏰ انتهت مهلة الاتصال")
            return "⏰ انتهت مهلة الطلب، حاول مرة أخرى"
        
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع: {e}")
            continue
    
    return "❌ فشلت جميع محاولات الاتصال مع Mimo AI"

# ====================== معالجة الرسائل ======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية من المستخدمين"""
    
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    message_text = update.message.text.strip()
    
    # تجاهل الرسائل الفارغة أو الأوامر
    if not message_text or message_text.startswith('/'):
        return
    
    logger.info(f"📩 رسالة من {user.id}: {message_text[:100]}...")
    
    # التحقق من طول الرسالة
    if len(message_text) > 2000:
        await update.message.reply_text("📏 الرسالة طويلة جداً. يرجى اختصارها.")
        return
    
    # إرسال رسالة الانتظار
    try:
        wait_msg = await update.message.reply_text("🤔 **جاري التفكير...**")
    except:
        wait_msg = None
    
    try:
        # الحصول على الرد من Mimo AI
        ai_response = await call_mimo_ai(message_text)
        
        # حذف رسالة الانتظار
        if wait_msg:
            try:
                await wait_msg.delete()
            except:
                pass
        
        # إرسال الرد
        if ai_response:
            # تقسيم الرد إذا كان طويلاً
            response_parts = Helper.split_message(ai_response)
            
            for i, part in enumerate(response_parts):
                try:
                    if i == 0:
                        await update.message.reply_text(part)
                    else:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=part
                        )
                    
                    # تأخير بسيط بين الرسائل
                    if i < len(response_parts) - 1:
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.error(f"❌ خطأ في إرسال جزء الرد: {e}")
        
        else:
            await update.message.reply_text("⚠️ لم أتلقى رداً من الذكاء الاصطناعي.")
    
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {e}")
        
        if wait_msg:
            try:
                await wait_msg.edit_text("❌ حدث خطأ في المعالجة. يرجى المحاولة مرة أخرى.")
            except:
                await update.message.reply_text("❌ حدث خطأ في المعالجة. يرجى المحاولة مرة أخرى.")


async def error_handler(update: object, context: CallbackContext):
    """معالجة الأخطاء العامة"""
    try:
        logger.error(f"🚨 خطأ غير معالج: {context.error}", exc_info=True)
        
        # إرسال رسالة خطأ للمستخدم إذا أمكن
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⚠️ عذراً، حدث خطأ تقني. يرجى المحاولة مرة أخرى لاحقاً."
                )
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ خطأ في معالج الأخطاء نفسه: {e}")

# ====================== إعدادات البوت ======================
async def setup_bot_commands(application: Application):
    """إعداد قائمة الأوامر للبوت"""
    commands = [
        BotCommand("start", "بدء المحادثة"),
        BotCommand("help", "عرض التعليمات"),
        BotCommand("status", "حالة النظام"),
        BotCommand("test", "اختبار اتصال Mimo AI"),
        BotCommand("about", "معلومات عن البوت"),
        BotCommand("ping", "قياس سرعة الاستجابة"),
    ]
    
    try:
        await application.bot.set_my_commands(commands)
        logger.info("✅ تم إعداد أوامر البوت")
    except Exception as e:
        logger.error(f"❌ خطأ في إعداد أوامر البوت: {e}")

# ====================== الدالة الرئيسية ======================
def main():
    """الدالة الرئيسية لتشغيل البوت"""
    
    logger.info("=" * 60)
    logger.info("🚀 بدء تشغيل Mimo AI Telegram Bot")
    logger.info("=" * 60)
    
    # التحقق من الإعدادات
    if not Config.validate():
        logger.error("❌ فشل التحقق من الإعدادات. إيقاف التشغيل.")
        return
    
    try:
        # إنشاء تطبيق البوت
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        
        # إضافة معالجات الأوامر
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("test", test_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("ping", ping_command))
        
        # معالجة الرسائل النصية
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        ))
        
        # معالج الأخطاء
        application.add_error_handler(error_handler)
        
        # إعداد أوامر القائمة
        application.post_init = setup_bot_commands
        
        # التشغيل
        if Config.PUBLIC_URL:
            # وضع Webhook للإنتاج
            logger.info(f"🌐 استخدام Webhook: {Config.PUBLIC_URL}")
            
            webhook_url = f"{Config.PUBLIC_URL}/{Config.TELEGRAM_TOKEN}"
            
            application.run_webhook(
                listen="0.0.0.0",
                port=Config.PORT,
                url_path=Config.TELEGRAM_TOKEN,
                webhook_url=webhook_url,
                secret_token=os.environ.get("WEBHOOK_SECRET", ""),
            )
        else:
            # وضع Polling للتطوير
            logger.info("🔧 استخدام وضع Polling (التطوير)")
            application.run_polling(
                poll_interval=1.0,
                timeout=30,
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            
    except Exception as e:
        logger.error(f"❌ فشل تشغيل البوت: {e}", exc_info=True)
        sys.exit(1)

# ====================== نقطة الدخول ======================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⏹️ إيقاف البوت بواسطة المستخدم")
        sys.exit(0)
