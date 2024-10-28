import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup
import base64
import json
import random

# Thiết lập API Tokens và cấu hình
TELEGRAM_TOKEN = '7846872870:AAEclA89Hy3i84FqPuh0ozFaHp4wFWLclFg'
wordpress_url = 'https://doanhnghiepchinhsach.vn'

# Danh sách tài khoản tác giả
AUTHORS = [
    {"username": "pv01", "password": "CGPP iFrW sC6w N4o1 lM1a Temy"},
    {"username": "dncs_user", "password": "lS6s cUHU a5Fr PXfa 2Krl cCxY"},
    {"username": "dreamitvn", "password": "waxA US8m 3XtO anbm Kc1x w4TT"}
]

# Danh mục và ID danh mục
CATEGORIES = { 
    "Chính sách": 8,
    "Công Nghệ": 22,
    "Doanh nghiệp": 12,
    "Kinh Doanh": 20,
    "Pháp luật": 21,
    "Tài Chính": 2,
    "Thương hiệu": 7,
    "Nhìn ra thế giới": 19,
    "Tin chính phủ": 43,
    "Tin trong nước": 1
}

async def extract_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else "Không có tiêu đề"
        content = ''.join([p.get_text() for p in soup.find_all('p')])
        
        # Lấy URL ảnh
        image_tags = soup.find_all('img')
        image_urls = [img['src'] for img in image_tags if 'src' in img.attrs]
        
        return {"title": title, "content": content, "image_urls": image_urls}
    except Exception as e:
        logging.error(f"Lỗi khi phân tích nội dung từ URL: {e}")
        return None

def upload_image_to_wordpress(image_url, wp_user, wp_password):
    try:
        image_data = requests.get(image_url).content
        file_name = image_url.split('/')[-1]
        files = {'file': (file_name, image_data, 'image/jpeg')}
        
        auth_header = {
            'Authorization': 'Basic ' + base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode('utf-8'),
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{wordpress_url}/wp-json/wp/v2/media",
            headers=auth_header,
            files=files
        )
        
        response_json = response.json()
        return response_json.get('id') if response.ok else None
    except Exception as e:
        logging.error(f"Lỗi khi tải ảnh lên WordPress: {e}")
        return None

def create_wordpress_post(title, content, category_id, image_id=None, wp_user=None, wp_password=None):
    try:
        auth_header = {
            'Authorization': 'Basic ' + base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode('utf-8'),
            'Content-Type': 'application/json'
        }
        
        data = {
            'title': title,
            'content': content,
            'status': 'publish',
            'categories': [category_id]
        }
        if image_id:
            data['featured_media'] = image_id
        
        response = requests.post(
            f"{wordpress_url}/wp-json/wp/v2/posts",
            headers=auth_header,
            json=data
        )
        
        response_json = response.json()
        return response_json if response.ok else None
    except Exception as e:
        logging.error(f"Lỗi khi đăng bài viết lên WordPress: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if url.startswith('http'):
        article_data = await extract_article_content(url)
        
        if not article_data:
            await update.message.reply_text("Không thể phân tích nội dung từ URL.")
            return
        
        # Chọn ngẫu nhiên tài khoản tác giả
        author = random.choice(AUTHORS)
        wp_user = author["username"]
        wp_password = author["password"]
        
        # Chọn ngẫu nhiên danh mục
        category_name = random.choice(list(CATEGORIES.keys()))
        category_id = CATEGORIES[category_name]
        
        image_id = None
        if article_data['image_urls']:
            image_id = upload_image_to_wordpress(article_data['image_urls'][0], wp_user, wp_password)
            if not image_id:
                await update.message.reply_text("Không thể tải ảnh lên WordPress.")
        
        new_post = create_wordpress_post(article_data['title'], article_data['content'], category_id, image_id, wp_user, wp_password)
        if new_post:
            await update.message.reply_text(f"Bài viết đã được đăng: {new_post.get('link')}")
        else:
            await update.message.reply_text("Có lỗi xảy ra khi đăng bài viết.")
    else:
        await update.message.reply_text("Vui lòng gửi một URL hợp lệ.")

def main():
    logging.basicConfig(level=logging.INFO)
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
