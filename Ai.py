# main.py
# بوت تلغرام مدمج مع Mimo AI
# تم الترجمة والتعريب بالكامل

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import aiohttp
import json

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- الحصول على الإعدادات من متغيرات البيئة ---
# قم بتعيين هذه المتغيرات في إعدادات Railway
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8087198006:AAH-7gvmZVbJ6oAVVXFlN1WxlU9jguEJMPU")
MIMO_AI_API_KEY = os.environ.get("MIMO_AI_API_KEY", "sk-sov58487uq7vxn9ytw1xedvbvpgss6crm3if4nq4qqapr4cw")
# Railway يوفر هذا المتغير تلقائياً
PUBLIC_URL = os.environ.get("RAILWAY_STATIC_URL", "") or os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")

# ملاحظة: تحتاج إلى معرفة رابط API الحقيقي لـ Mimo AI
MIMO_AI_API_URL = os.environ.get("MIMO_AI_API_URL", "https://api.mimo.ai/v1/chat/completions")

# --- معالجة أمر /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"مرحباً {user.first_name}! 👋\n"
        f"أنا مساعدك Darck AI الذكي.\n\n"
        f"📝 فقط أرسل لي رسالة وسأرد عليك باستخدام الذكاء الاصطناعي.\n"
        f"🔧 الحالة: {'✅ متصل بـ Mimo AI' if MIMO_AI_API_KEY else '⚠️ لم يتم ضبط مفتاح AI'}"
    )

# --- معالجة أمر /help ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    📚 **الأوامر المتاحة:**

    /start - بدء استخدام البوت
    /help - عرض رسالة المساعدة هذه
    /status - التحقق من حالة البوت

    💬 **طريقة الاستخدام:**
    فقط أرسل لي أي رسالة وسأرد عليك باستخدام الذكاء الاصطناعي!

    🔒 **معلومات الأمان:**
    البوت لا يحفظ محادثاتك الخاصة.
    """
    await update.message.reply_text(help_text)

# --- معالجة أمر /status ---
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = "✅ **البوت يعمل بشكل طبيعي**\n"
    
    if PUBLIC_URL:
        status += f"🌐 **الرابط العام:** {PUBLIC_URL}\n"
    else:
        status += "⚠️ **لم يتم ضبط Webhook** (وضع التحديث المستخدم)\n"
    
    if MIMO_AI_API_KEY.startswith("sk-"):
        status += "🤖 **Mimo AI:** متصل ✅\n"
    else:
        status += "🤖 **Mimo AI:** غير متصل ❌\n"
    
    await update.message.reply_text(status)

# --- دالة للاتصال بـ Mimo AI API ---
async def call_mimo_ai(prompt: str):
    """الاتصال بـ Mimo AI API للحصول على رد"""
    
    if not MIMO_AI_API_KEY or MIMO_AI_API_KEY == "مفتاح_API_الخاص_بك_هنا":
        return "⚠️ **خطأ:** لم يتم ضبط مفتاح Mimo AI API. يرجى التحقق من إعدادات متغيرات البيئة."
    
    # إعدادات الطلب (نفترض توافقها مع OpenAI API)
    headers = {
        "Authorization": f"Bearer {MIMO_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # هيكل البيانات (يجب تعديله حسب وثائق Mimo AI الرسمية)
    data = {
        "model": "gpt-3.5-turbo",  # أو اسم النموذج الذي تحدده Mimo AI
        "messages": [
            {"role": "system", "content": "أنت مساعد مفيد يتحدث العربية."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    try:
        # تعيين مهلة 30 ثانية للطلب
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(MIMO_AI_API_URL, headers=headers, json=data) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # محاولة تحليل الرد (يجب تعديله حسب هيكل API الحقيقي)
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"].strip()
                    elif "text" in result:
                        return result["text"].strip()
                    else:
                        return f"⚠️ **تم استقبال رد ولكن بصيغة غير معروفة:** {json.dumps(result)[:200]}..."
                
                else:
                    error_text = await response.text()
                    logger.error(f"خطأ في Mimo API {response.status}: {error_text}")
                    return f"⚠️ **خدمة الذكاء الاصطناعي غير متاحة حالياً** (خطأ {response.status})"
    
    except asyncio.TimeoutError:
        return "⏳ **انتهت مهلة الطلب، يرجى المحاولة مرة أخرى لاحقاً.**"
    
    except Exception as e:
        logger.error(f"خطأ في الاتصال بـ Mimo AI: {str(e)}")
        return f"⚠️ **حدث خطأ في معالجة طلبك:** {str(e)[:100]}"

# --- معالجة الرسائل النصية العادية ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # معالجة الرسائل الخاصة فقط
    if update.message.chat.type != "private":
        return
    
    user_message = update.message.text
    user = update.effective_user
    logger.info(f"المستخدم @{user.username or user.id} قال: {user_message[:50]}...")
    
    # إرسال رسالة "جاري التفكير"
    try:
        processing_msg = await update.message.reply_text("🧠 **جاري التفكير، يرجى الانتظار...**")
    except:
        processing_msg = None
    
    try:
        # الاتصال بـ Mimo AI
        ai_response = await call_mimo_ai(user_message)
        
        # إرسال الرد
        if processing_msg:
            await processing_msg.delete()
        
        # إذا كان الرد طويلاً، تقسيمه إلى أجزاء
        if len(ai_response) > 4000:
            chunks = [ai_response[i:i+4000] for i in range(0, len(ai_response), 4000)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await update.message.reply_text(chunk)
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=chunk
                    )
        else:
            await update.message.reply_text(ai_response)
            
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}")
        if processing_msg:
            await processing_msg.edit_text("⚠️ **عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى لاحقاً.**")
        else:
            await update.message.reply_text("⚠️ **عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى لاحقاً.**")

# --- معالجة الأخطاء ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"حدث خطأ: {context.error}")
    # يمكنك إضافة كود هنا لإرسال تقارير الأخطاء إلى المدير

# --- الدالة الرئيسية ---
def main():
    logger.info("جاري تشغيل بوت Darck AI...")
    
    # التحقق من الإعدادات الأساسية
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "مفتاح_البوت_الخاص_بك_هنا":
        logger.error("⚠️ **لم يتم ضبط مفتاح Telegram Bot Token!**")
        print("""
        ⚠️ **تنبيه مهم:**
        يرجى تعيين متغير البيئة TELEGRAM_BOT_TOKEN
        في إعدادات Railway أو في ملف .env محلياً.
        """)
        return
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_message))
    application.add_error_handler(error_handler)
    
    # التحقق إذا كان يعمل على Railway
    if PUBLIC_URL:
        # وضع Webhook (للإنتاج على Railway)
        logger.info(f"جاري استخدام وضع Webhook، الرابط: {PUBLIC_URL}")
        
        # ضبط Webhook
        webhook_url = f"{PUBLIC_URL}/{TELEGRAM_BOT_TOKEN}"
        
        async def set_webhook():
            await application.bot.set_webhook(webhook_url)
            logger.info(f"تم ضبط Webhook على: {webhook_url}")
        
        # تشغيل Webhook
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8080)),
            webhook_url=webhook_url,
            url_path=TELEGRAM_BOT_TOKEN,
            secret_token=os.environ.get("WEBHOOK_SECRET", ""),
        )
    else:
        # وضع التحديث (للتطوير المحلي)
        logger.info("جاري استخدام وضع التحديث (للتطوير المحلي)")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
