import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 设置日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 配置信息 ---
# 请将以下密钥替换为你的实际密钥
TELEGRAM_BOT_TOKEN = "8087198006:AAH-7gvmZVbJ6oAVVXFlN1WxlU9jguEJMPU"
MIMO_AI_API_KEY = "sk-sov58487uq7vxn9ytw1xedvbvpgss6crm3if4nq4qqapr4cw"  # 请用你的完整API密钥替换
MIMO_AI_API_URL = "https://api.mimo.ai/v1/chat/completions"  # 注意：此为假设的Mimo AI端点

# --- 处理 /start 命令 ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"你好 {user.first_name}！我是你的Darck AI助手。\n请直接发送消息，我会尝试用AI进行回复。"
    )

# --- 处理普通文本消息 ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"用户 {chat_id} 说: {user_message}")

    # 发送“正在思考”状态
    processing_msg = await update.message.reply_text("🧠 正在思考，请稍候...")

    try:
        # 调用AI API获取回复
        ai_response = await call_mimo_ai(user_message)
        # 删除“正在思考”消息，并发送AI回复
        await processing_msg.delete()
        await update.message.reply_text(ai_response)
    except Exception as e:
        logger.error(f"调用AI API时出错: {e}")
        await processing_msg.edit_text("抱歉，处理你的请求时出错了。请稍后再试。")

# --- 调用Mimo AI API的函数 ---
async def call_mimo_ai(prompt: str):
    import aiohttp
    import json

    # 构造请求头（假设Mimo AI与OpenAI API兼容）
    headers = {
        "Authorization": f"Bearer {MIMO_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    # 构造请求数据（根据Mimo AI的实际API文档调整）
    data = {
        "model": "gpt-3.5-turbo",  # 或Mimo AI指定的模型名
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }

    # 使用aiohttp异步发送请求
    async with aiohttp.ClientSession() as session:
        async with session.post(MIMO_AI_API_URL, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                # 解析回复（根据实际API响应结构调整）
                return result["choices"][0]["message"]["content"].strip()
            else:
                error_text = await response.text()
                raise Exception(f"API错误 {response.status}: {error_text}")

# --- 处理错误 ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"更新 {update} 导致错误: {context.error}")
    # 可以在这里添加向特定用户或管理员发送错误报告的代码

# --- 主函数 ---
def main():
    # 创建应用实例
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    # 添加消息处理器（只处理私聊文本消息）
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_message))
    # 添加错误处理器
    application.add_error_handler(error_handler)

    # 启动Bot（Webhook模式，适用于Railway部署）
    port = int(os.environ.get("PORT", 8080))
    webhook_url = os.environ.get("RAILWAY_STATIC_URL")  # Railway提供的动态URL
    if webhook_url:
        # Webhook模式（生产环境）[citation:8]
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TELEGRAM_BOT_TOKEN,
            webhook_url=f"{webhook_url}/{TELEGRAM_BOT_TOKEN}"
        )
        logger.info(f"Webhook模式启动在 {webhook_url}")
    else:
        # Polling模式（本地开发）[citation:6]
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Polling模式启动")

if __name__ == "__main__":
    main()
