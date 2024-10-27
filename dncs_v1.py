import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup
import base64

# 1. Thiết lập API Keys và Token
TELEGRAM_TOKEN = '7846872870:AAEclA89Hy3i84FqPuh0ozFaHp4wFWLclFg'

# 2. Cấu hình thông tin WordPress
wordpress_url = 'https://doanhnghiepchinhsach.vn/'
wp_user = 'pv01'
wp_password = '3XXo 2dqL AJ08 IGrp RYVa ukBQ'

auth_header = {
    'Authorization': 'Basic ' + base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode('utf-8'),
    'Content-Type': 'application/json'
}

async def extract_article_content(url):
    # (Hàm này giữ nguyên như hướng dẫn trước)
    # Hàm thực hiện phân tích nội dung từ URL và trả về dữ liệu bài viết và ảnh.

async def upload_image_to_wordpress(image_url):
    # (Hàm này giữ nguyên như hướng dẫn trước)
    # Hàm thực hiện tải ảnh lên WordPress và trả về `image_id`.

async def create_wordpress_post(title, content, image_id=None):
    # (Hàm này giữ nguyên như hướng dẫn trước)
    # Hàm thực hiện đăng bài viết lên WordPress và trả về `post_id`.

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if url.startswith('http'):
        article_data = await extract_article_content(url)
        
        if not article_data:
            await update.message.reply_text("Không thể phân tích nội dung từ URL. Vui lòng kiểm tra lại.")
            return
        
        # Đăng ảnh lên WordPress nếu có
        image_id = None
        if article_data['image_urls']:
            image_id = await upload_image_to_wordpress(article_data['image_urls'][0])
            if not image_id:
                await update.message.reply_text("Không thể tải ảnh lên WordPress.")
        
        # Đăng bài lên WordPress
        new_post = await create_wordpress_post(article_data['title'], article_data['content'], image_id)
        if new_post:
            await update.message.reply_text(f"Bài viết đã được đăng: {new_post.get('link')}")
        else:
            await update.message.reply_text("Có lỗi xảy ra khi đăng bài viết.")
    else:
        await update.message.reply_text("Vui lòng gửi một URL hợp lệ.")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
