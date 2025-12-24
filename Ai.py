#!/usr/bin/env python3
"""
بوت تلغرام ذكي مع Mimo AI
إصدار مستقر ومدمج بالكامل
"""

import os
import sys
import logging
import asyncio
from typing import Optional
from datetime import datetime

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
import json

# ====================== إعدادات التسجيل ======================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ====================== الإعدادات ======================
class Config:
    """إعدادات التطبيق"""
    
    # مفاتيح API (من متغيرات البيئة أولاً)
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8087198006:AAH-7gvmZVbJ6oAVVXFlN1WxlU9jguEJMPU")
    MIMO_API_KEY = os.environ.get("MIMO_AI_API_KEY", "sk-sov58487uq7vxn9ytw1xedvbvpgss6crm3if4nq4qqapr4cw")
    
    # روابط API
    MIMO_API_URL = os.environ.get("MIMO_AI_API_URL", "https://api.mimo.ai/v1/chat/completions")
    TELEGRAM_API = "https://api.telegram.org/bot"
    
    # إعدادات Railway
    PORT = int(os.environ.get("PORT", 8080))
    PUBLIC_URL = os.environ.get("RAILWAY_STATIC_URL", "") or os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    
    # إعدادات البوت
    BOT_USERNAME = "@darck_ai_bot"
    MAX_MESSAGE_LENGTH = 4096
    REQUEST_TIMEOUT = 30
    
    @classmethod
    def validate(cls):
        """التحقق من صحة الإعدادات"""
        errors = []
        
        if not cls.TELEGRAM_TOKEN or cls.TELEGRAM_TOKEN == "ضع_مفتاح_البوت_هنا":
            errors.append("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN")
        
        if not cls.MIMO_API_KEY or cls.MIMO_API_KEY == "ضع_مفتاح_Mimo_هنا":
            errors.append("⚠️ لم يتم تعيين MIMO_AI_API_KEY")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False
        
        logger.info("✅ جميع الإعدادات صحيحة")
        return True

# ====================== دوال المساعدة ======================
class Helper:
    """دوال المساعدة العامة"""
    
    @staticmethod
    async def split_long_message(text: str, max_length: int = 4000):
        """تقسيم الرسائل الطويلة"""
        if len(text) <= max_length:
            return [text]
        
        parts = []
        while text:
            if len(text) <= max_length:
                parts.append(text)
                break
            
            # البحث عن آخر مسافة للقطع
            split_index = text[:max_length].rfind(' ')
            if split_index == -1:
                split_index = max_length
            
            parts.append(text[:split_index])
            text = text[split_index:].strip()
        
        return parts
    
    @staticmethod
    def get_current_time():
        """الحصول على الوقت الحالي"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    async def internet_available():
        """التحقق من اتصال الإنترنت"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.telegram.org", timeout=5) as response:
                    return response.status == 200
        except:
            return False

# ====================== معالجات الأوامر ======================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /start"""
    user = update.effective_user
    
    welcome_text = f"""
🎉 **مرحباً {user.first_name}!**

أنا **Darck AI**، بوت الذكاء الاصطناعي المتطور.

✨ **الميزات:**
• محادثات ذكية مع Mimo AI
• دعم اللغة العربية
• سرعة في الرد
• تشفير آمن

🔧 **الأوامر المتاحة:**
/start - بدء المحادثة
/help - عرض المساعدة
/status - حالة النظام
/about - معلومات عن البوت
/settings - الإعدادات (قريباً)

📝 **كيفية الاستخدام:**
فقط أرسل رسالة وسأرد عليك فوراً!

⚡ **الحالة:** {Helper.get_current_time()}
"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    # تسجيل دخول المستخدم
    logger.info(f"مستخدم جديد: {user.id} - {user.username or 'بدون اسم'}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /help"""
    help_text = """
📚 **دليل المستخدم الكامل**

🔹 **الأوامر الأساسية:**
/start - بدء المحادثة
/help - عرض هذه الرسالة
/status - حالة النظام والخوادم
/about - معلومات عن البوت
/ping - اختبار سرعة الاستجابة

🔹 **الميزات المتقدمة:**
• محادثات ذكية باللغة العربية
• دعم الرسائل الطويلة
• حفظ سياق المحادثة
• معالجة الأخطاء التلقائية

🔹 **نصائح للاستخدام:**
1. استخدم جمل كاملة للحصول على ردود أفضل
2. يمكنك السؤال عن أي موضوع
3. البوت يدعم التنسيق النصي الأساسي
4. الردود تستغرق من 2-5 ثوانٍ

🔹 **الدعم التقني:**
في حال وجود مشاكل:
1. تحقق من اتصال الإنترنت
2. استخدم /status للتحقق
3. أعد إرسال الرسالة
4. تواصل مع المطور

🛠️ **الإصدار:** 2.0.0
📅 **آخر تحديث:** 2024-12-24
"""
    
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: CallbackContext):
    """معالجة أمر /status"""
    
    # جمع معلومات النظام
    status_info = []
    
    # حالة البوت الأساسية
    status_info.append("📊 **حالة النظام**")
    status_info.append(f"🕐 الوقت: {Helper.get_current_time()}")
    
    # حالة اتصال الإنترنت
    internet_status = await Helper.internet_available()
    status_info.append(f"🌐 الإنترنت: {'✅ متصل' if internet_status else '❌ غير متصل'}")
    
    # حالة Mimo AI
    if Config.MIMO_API_KEY and Config.MIMO_API_KEY != "ضع_مفتاح_Mimo_هنا":
        status_info.append("🤖 Mimo AI: ✅ متاح")
    else:
        status_info.append("🤖 Mimo AI: ⚠️ غير مضبوط")
    
    # حالة Railway
    if Config.PUBLIC_URL:
        status_info.append(f"🚄 Railway: ✅ {Config.PUBLIC_URL[:30]}...")
    else:
        status_info.append("🚄 Railway: ⚠️ وضع التطوير")
    
    # حالة الذاكرة
    import psutil
    memory = psutil.virtual_memory()
    status_info.append(f"💾 الذاكرة: {memory.percent}% مستخدم")
    
    # حالة التحديثات
    status_info.append(f"📈 الرسائل المعالجة: {len(context.chat_data.get('messages', [])) if context.chat_data else 0}")
    
    # إرسال الرسالة
    status_text = "\n".join(status_info)
    await update.message.reply_text(status_text, parse_mode='Markdown')


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /about"""
    about_text = """
🤖 **Darck AI Bot**

**وصف:**
بوت تلغرام ذكي يعمل بالذكاء الاصطناعي من Mimo AI.
مصمم خصيصاً للمحادثات الذكية باللغة العربية.

**الميزات:**
• محرك Mimo AI المتقدم
• دعم اللغة العربية الكامل
• تصميم سريع ومستقر
• تشفير آمن للبيانات
• معالجة ذكية للرسائل

**التقنيات المستخدمة:**
• Python 3.11+
• python-telegram-bot 21.7
• Mimo AI API
• Railway للاستضافة

**المطور:**
تم تطويره بواسطة فريق Darck AI
لتقديم تجربة محادثة استثنائية.

📞 **للتواصل والدعم:**
@darck_ai_bot

📄 **الرخصة:**
مشروع مفتوح المصدر للأغراض التعليمية.

✨ **شعارنا:**
ذكاء اصطناعي بلمسة إنسانية!
"""
    
    await update.message.reply_text(about_text)


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /ping"""
    start_time = datetime.now()
    message = await update.message.reply_text("🏓 بينج...")
    end_time = datetime.now()
    
    response_time = (end_time - start_time).total_seconds() * 1000
    
    await message.edit_text(f"🏓 بونج!\n⚡ وقت الاستجابة: {response_time:.2f} مللي ثانية")


# ====================== Mimo AI Integration ======================
class MimoAI:
    """فئة للتعامل مع Mimo AI API"""
    
    @staticmethod
    async def generate_response(prompt: str) -> str:
        """إنشاء رد باستخدام Mimo AI"""
        
        # التحقق من المفتاح
        if not Config.MIMO_API_KEY or Config.MIMO_API_KEY == "ضع_مفتاح_Mimo_هنا":
            return "⚠️ عذراً، لم يتم ضبط مفتاح Mimo AI API.\nيرجى التحقق من الإعدادات."
        
        # إعدادات الطلب
        headers = {
            "Authorization": f"Bearer {Config.MIMO_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Darck-AI-Bot/2.0.0"
        }
        
        # بناء البيانات
        data = {
            "model": "gpt-4",  # أو أي نموذج تدعمه Mimo AI
            "messages": [
                {
                    "role": "system",
                    "content": """أنت مساعد ذكي يتحدث العربية بطلاقة.
                    يجب أن تكون ردودك مفيدة ودقيقة وودية.
                    استخدم تنسيق Markdown البسيط عند الحاجة.
                    إذا لم تعرف إجابة، قل ذلك بصراحة.
                    حافظ على الردود باللغة العربية ما لم يطلب خلاف ذلك."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        
        try:
            logger.info(f"إرسال طلب إلى Mimo AI: {prompt[:50]}...")
            
            # إرسال الطلب
            timeout = aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    Config.MIMO_API_URL,
                    headers=headers,
                    json=data,
                    ssl=False  # قد تحتاج لتفعيله في الإنتاج
                ) as response:
                    
                    # تسجيل الاستجابة
                    logger.info(f"استجابة Mimo AI: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # تحليل الاستجابة (تعديل حسب هيكل Mimo AI)
                        try:
                            if "choices" in result:
                                message_content = result["choices"][0]["message"]["content"]
                            elif "text" in result:
                                message_content = result["text"]
                            elif "response" in result:
                                message_content = result["response"]
                            else:
                                message_content = str(result)[:500]
                            
                            return message_content.strip()
                            
                        except (KeyError, IndexError) as e:
                            logger.error(f"خطأ في تحليل الرد: {e}")
                            return "⚠️ حدث خطأ في معالجة الاستجابة. يرجى المحاولة مرة أخرى."
                    
                    elif response.status == 401:
                        return "❌ خطأ في المصادقة. يرجى التحقق من مفتاح API."
                    
                    elif response.status == 429:
                        return "⚠️ تجاوز الحد المسموح. يرجى الانتظار قليلاً."
                    
                    elif response.status == 503:
                        return "🔧 الخدمة غير متاحة حالياً. يرجى المحاولة لاحقاً."
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"خطأ API: {response.status} - {error_text[:200]}")
                        return f"⚠️ خطأ في الخادم (رمز {response.status})"

        except asyncio.TimeoutError:
            logger.error("انتهت مهلة طلب Mimo AI")
            return "⏰ انتهت مهلة الطلب. يرجى المحاولة مرة أخرى."
        
        except aiohttp.ClientError as e:
            logger.error(f"خطأ اتصال: {e}")
            return "🌐 مشكلة في الاتصال بالخادم. تحقق من اتصال الإنترنت."
        
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {e}")
            return f"⚠️ حدث خطأ غير متوقع: {str(e)[:100]}"


# ====================== معالجة الرسائل ======================
async def handle_message(update: Update, context: CallbackContext):
    """معالجة جميع الرسائل النصية"""
    
    # التحقق من الرسالة
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    message_text = update.message.text.strip()
    
    # تسجيل الرسالة
    logger.info(f"رسالة من {user.id}: {message_text[:100]}...")
    
    # تجاهل الأوامر (تم معالجتها بواسطة handlers)
    if message_text.startswith('/'):
        return
    
    # التحقق من الرسائل الطويلة جداً
    if len(message_text) > 2000:
        await update.message.reply_text("📝 الرسالة طويلة جداً. يرجى اختصارها إلى أقل من 2000 حرف.")
        return
    
    # إرسال رسالة الانتظار
    try:
        wait_message = await update.message.reply_text("🤔 **جاري التفكير...**")
    except Exception as e:
        logger.error(f"خطأ في إرسال رسالة الانتظار: {e}")
        wait_message = None
    
    # الحصول على الرد من AI
    try:
        ai_response = await MimoAI.generate_response(message_text)
        
        # حذف رسالة الانتظار
        if wait_message:
            try:
                await wait_message.delete()
            except:
                pass
        
        # إرسال الرد
        if ai_response:
            # تقسيم الرد إذا كان طويلاً
            response_parts = await Helper.split_long_message(ai_response)
            
            for i, part in enumerate(response_parts):
                try:
                    if i == 0:
                        await update.message.reply_text(part, parse_mode='Markdown')
                    else:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=part,
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    logger.error(f"خطأ في إرسال جزء الرد: {e}")
                    # المحاولة بدون Markdown
                    try:
                        if i == 0:
                            await update.message.reply_text(part)
                        else:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=part
                            )
                    except:
                        await update.message.reply_text("⚠️ حدث خطأ في إرسال الرد.")
        else:
            await update.message.reply_text("⚠️ لم يتم استلام رد من الذكاء الاصطناعي.")
    
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}")
        
        if wait_message:
            try:
                await wait_message.edit_text("❌ حدث خطأ في المعالجة. يرجى المحاولة مرة أخرى.")
            except:
                await update.message.reply_text("❌ حدث خطأ في المعالجة. يرجى المحاولة مرة أخرى.")


async def error_handler(update: object, context: CallbackContext):
    """معالجة الأخطاء العامة"""
    try:
        logger.error(f"حدث خطأ: {context.error}", exc_info=True)
        
        # يمكنك إضافة منطق إرسال الأخطاء إلى المدير هنا
        error_msg = f"⚠️ خطأ في النظام: {str(context.error)[:200]}"
        
        # إرسال رسالة خطأ للمستخدم إذا كان هناك update
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "عذراً، حدث خطأ تقني. يرجى المحاولة مرة أخرى لاحقاً."
                )
            except:
                pass
                
    except Exception as e:
        logger.error(f"خطأ في معالج الأخطاء نفسه: {e}")


# ====================== إعدادات البوت ======================
async def setup_bot_commands(application: Application):
    """إعداد أوامر القائمة للبوت"""
    commands = [
        BotCommand("start", "بدء المحادثة"),
        BotCommand("help", "عرض التعليمات"),
        BotCommand("status", "حالة النظام"),
        BotCommand("about", "معلومات عن البوت"),
        BotCommand("ping", "اختبار الاستجابة"),
    ]
    
    try:
        await application.bot.set_my_commands(commands)
        logger.info("✅ تم إعداد أوامر البوت")
    except Exception as e:
        logger.error(f"خطأ في إعداد أوامر البوت: {e}")


# ====================== الدالة الرئيسية ======================
def main():
    """الدالة الرئيسية لتشغيل البوت"""
    
    logger.info("=" * 50)
    logger.info("🚀 بدء تشغيل Darck AI Bot")
    logger.info("=" * 50)
    
    # التحقق من الإعدادات
    if not Config.validate():
        logger.error("❌ فشل التحقق من الإعدادات. إيقاف التشغيل.")
        return
    
    try:
        # إنشاء تطبيق البوت
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        
        # إعداد المعالجات
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("ping", ping_command))
        application.add_handler(CommandHandler("settings", help_command))  # مؤقت
        
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
            logger.info("🔧 استخدام وضع Polling للتطوير")
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
