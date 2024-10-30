from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from dangbai import dang_bai  # Giả sử bạn có hàm dang_bai trong dangbai.py
from danlai1 import dan_lai     # Giả sử bạn có hàm dan_lai trong danlai.py
from fb1 import post_facebook   # Giả sử bạn có hàm post_facebook trong fb1.py

# Tải biến môi trường từ file .env
load_dotenv()  
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Kiểm tra xem TELEGRAM_BOT_TOKEN có hợp lệ không
if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN không được thiết lập trong file .env.")

# Hàm chính khởi chạy bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Xin chào! Sử dụng /dangbai, /danlai, hoặc /postfb để thực hiện chức năng tương ứng.")

# Hàm xử lý lệnh /dangbai
async def handle_dangbai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        message_text = " ".join(context.args)
        result = dang_bai(message_text)  # Gọi hàm để đăng bài
        await update.message.reply_text(result)
    else:
        await update.message.reply_text("Vui lòng cung cấp nội dung để đăng bài.")

# Hàm xử lý lệnh /danlai
async def handle_danlai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        message_text = " ".join(context.args)
        result = dan_lai(message_text)  # Gọi hàm để dẫn lại
        await update.message.reply_text(result)
    else:
        await update.message.reply_text("Vui lòng cung cấp nội dung để dẫn lại.")

# Hàm xử lý lệnh /postfb
async def handle_postfb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        message_text = " ".join(context.args)
        result = post_facebook(message_text)  # Gọi hàm để post lên Facebook
        await update.message.reply_text(result)
    else:
        await update.message.reply_text("Vui lòng cung cấp link bài viết để đăng lên Facebook.")

# Hàm khởi chạy bot
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Đăng ký các handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dangbai", handle_dangbai))
    application.add_handler(CommandHandler("danlai", handle_danlai))
    application.add_handler(CommandHandler("postfb", handle_postfb))
    
    # Bắt đầu bot
    application.run_polling()

if __name__ == '__main__':
    main()
