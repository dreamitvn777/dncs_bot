from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
import os
from dotenv import load_dotenv
from dangbai import dang_bai  # Giả sử bạn có hàm dang_bai trong dangbai.py

# Define states for conversation
TITLE, CONTENT, TAGS, IMAGE, SAPO = range(5)

# Tải biến môi trường từ file .env
load_dotenv()  
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Hàm bắt đầu quy trình đăng bài
async def start_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Xin vui lòng nhập tiêu đề bài viết:")
    return TITLE

# Xử lý tiêu đề
async def title_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Xin vui lòng nhập nội dung bài viết:")
    return CONTENT

# Xử lý nội dung
async def content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['content'] = update.message.text
    await update.message.reply_text("Xin vui lòng nhập từ khóa bài viết (tags), hoặc nhập '.' để bỏ qua:")
    return TAGS

# Xử lý từ khóa
async def tags_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tags_input = update.message.text
    if tags_input != ".":
        context.user_data['tags'] = tags_input.split(",")  # Chia từ khóa theo dấu phẩy
    else:
        context.user_data['tags'] = []  # Bỏ qua
    await update.message.reply_text("Xin vui lòng nhập đường dẫn ảnh đại diện:")
    return IMAGE

# Xử lý ảnh đại diện
async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['image_path'] = update.message.text
    await update.message.reply_text("Xin vui lòng nhập sapo (mô tả ngắn), hoặc nhập '.' để bỏ qua:")
    return SAPO

# Xử lý sapo
async def sapo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sapo_input = update.message.text
    if sapo_input != ".":
        context.user_data['sapo'] = sapo_input
    else:
        context.user_data['sapo'] = None  # Bỏ qua
    await update.message.reply_text("Đang đăng bài...")
    result = dang_bai("", context.user_data)  # Gọi hàm đăng bài
    await update.message.reply_text(result)
    return ConversationHandler.END

# Hàm khởi chạy bot
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("dangbai", start_update)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_handler)],
            CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, content_handler)],
            TAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tags_handler)],
            IMAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, image_handler)],
            SAPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, sapo_handler)],
        },
        fallbacks=[],
    )

    # Đăng ký các handler
    application.add_handler(conv_handler)

    # Bắt đầu bot
    application.run_polling()

if __name__ == '__main__':
    main()
