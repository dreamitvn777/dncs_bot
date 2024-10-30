from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
from dangbai import dang_bai  # Giả sử bạn có hàm dang_bai trong dangbai.py
from danlai1 import dan_lai     # Giả sử bạn có hàm dan_lai trong danlai.py
from fb1 import post_facebook   # Giả sử bạn có hàm post_facebook trong fb1.py

# Tải biến môi trường từ file .env
load_dotenv()  
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Kiểm tra xem TELEGRAM_BOT_TOKEN có hợp lệ không
if TELEGRAM_TOKEN is None:
    raise ValueError("TELEGRAM_TOKEN không được thiết lập trong file .env.")

# Hàm chính khởi chạy bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Đăng Bài", callback_data='dangbai')],
        [InlineKeyboardButton("Dẫn Lại", callback_data='danlai')],
        [InlineKeyboardButton("Đăng lên Facebook", callback_data='postfb')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Xin chào! Vui lòng chọn một chức năng:", reply_markup=reply_markup)

# Hàm xử lý callback từ các nút
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'dangbai':
        await query.edit_message_text(text="Vui lòng nhập nội dung để đăng bài.")
        return  # Dừng lại để người dùng có thể gửi nội dung

    if query.data == 'danlai':
        await query.edit_message_text(text="Vui lòng nhập nội dung để dẫn lại.")
        return  # Dừng lại để người dùng có thể gửi nội dung

    if query.data == 'postfb':
        await query.edit_message_text(text="Vui lòng nhập link bài viết để đăng lên Facebook.")
        return  # Dừng lại để người dùng có thể gửi link

# Hàm xử lý tin nhắn từ người dùng
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text

    if context.user_data.get('current_action') == 'dangbai':
        result = dang_bai(message_text)  # Gọi hàm để đăng bài
        await update.message.reply_text(result)
        context.user_data['current_action'] = None  # Reset action

    elif context.user_data.get('current_action') == 'danlai':
        result = dan_lai(message_text)  # Gọi hàm để dẫn lại
        await update.message.reply_text(result)
        context.user_data['current_action'] = None  # Reset action

    elif context.user_data.get('current_action') == 'postfb':
        result = post_facebook(message_text)  # Gọi hàm để post lên Facebook
        await update.message.reply_text(result)
        context.user_data['current_action'] = None  # Reset action

    else:
        await update.message.reply_text("Vui lòng sử dụng các nút để chọn chức năng.")

# Hàm khởi chạy bot
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Đăng ký các handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))  # Xử lý callback từ nút
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Xử lý tin nhắn

    # Bắt đầu bot
    application.run_polling()

if __name__ == '__main__':
    main()
