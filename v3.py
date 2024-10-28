import logging
import requests
import base64
import json
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup

# Thiết lập logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Thiết lập API Tokens và cấu hình
TELEGRAM_TOKEN = '7846872870:AAEclA89Hy3i84FqPuh0ozFaHp4wFWLclFg'
wordpress_url = 'https://doanhnghiepchinhsach.vn/wp-json/wp/v2'
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

# Danh sách tài khoản tác giả
authors = [
    {"username": "pv01", "password": "CGPP iFrW sC6w N4o1 lM1a Temy"},
    {"username": "dncs_user", "password": "lS6s cUHU a5Fr PXfa 2Krl cCxY"},
    {"username": "dreamitvn", "password": "waxA US8m 3XtO anbm Kc1x w4TT"}
]

def get_random_author():
    return random.choice(authors)

async def extract_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Lấy tiêu đề
        title = soup.title.string if soup.title else "Không có tiêu đề"

        # Tìm phần nội dung chính
        content_section = soup.find('article') or soup.find('div', class_='content')
        content = ''

        if content_section:
            content_paragraphs = content_section.find_all('p')
            content = '\n'.join([p.get_text().strip() for p in content_paragraphs if p.get_text().strip()])
            content = content.split('bảo đảm an sinh xã hội.')[0].strip()  # Giới hạn nội dung

        # Lấy URL ảnh
        image_tags = soup.find_all('img')
        image_urls = [img['src'] for img in image_tags if 'src' in img.attrs]

        # Lấy phần tóm tắt
        summary = ''
        summary_tag = soup.find('meta', attrs={'name': 'description'})
        if summary_tag and 'content' in summary_tag.attrs:
            summary = summary_tag['content']
        elif content_paragraphs:
            summary = content_paragraphs[0].get_text()

        return {
            "title": title,
            "content": content,
            "summary": summary,
            "image_urls": image_urls
        }
    except Exception as e:
        print(f"Lỗi khi phân tích nội dung từ URL: {e}")
        return None

def upload_image_to_wordpress(image_url, auth_header):
    try:
        image_data = requests.get(image_url).content
        file_name = image_url.split('/')[-1]
        files = {'file': (file_name, image_data, 'image/jpeg')}
        
        response = requests.post(
            f"{wordpress_url}/media",
            headers=auth_header,
            files=files
        )

        response_json = response.json()
        return response_json.get('id') if response.ok else None
    except Exception as e:
        print(f"Lỗi khi tải ảnh lên WordPress: {e}")
        return None

def create_wordpress_post(title, content, category_id, image_id=None, auth_header=None):
    try:
        data = {
            'title': title,
            'content': content,
            'status': 'publish',
            'categories': [category_id]
        }
        if image_id:
            data['featured_media'] = image_id
        
        response = requests.post(
            f"{wordpress_url}/posts",
            headers=auth_header,
            json=data
        )

        response_json = response.json()
        return response_json if response.ok else None
    except Exception as e:
        print(f"Lỗi khi đăng bài viết lên WordPress: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if url.startswith('http'):
        article_data = await extract_article_content(url)
        
        if not article_data:
            await update.message.reply_text("Không thể phân tích nội dung từ URL.")
            return
        
        # Chọn danh mục
        await update.message.reply_text("Vui lòng chọn danh mục từ danh sách sau: " + ", ".join(CATEGORIES.keys()))
        
        # Lưu danh mục vào context
        context.user_data['article_data'] = article_data
        context.user_data['url'] = url
    else:
        await update.message.reply_text("Vui lòng gửi một URL hợp lệ.")

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    if category in CATEGORIES:
        # Lấy dữ liệu bài viết từ context
        article_data = context.user_data.get('article_data')
        url = context.user_data.get('url')

        # Lấy tài khoản tác giả ngẫu nhiên
        author = get_random_author()
        wp_user = author['username']
        wp_password = author['password']

        auth_header = {
            'Authorization': 'Basic ' + base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode('utf-8'),
            'Content-Type': 'application/json'
        }

        image_id = None
        if article_data['image_urls']:
            image_id = upload_image_to_wordpress(article_data['image_urls'][0], auth_header)
            if not image_id:
                await update.message.reply_text("Không thể tải ảnh lên WordPress.")

        new_post = create_wordpress_post(article_data['title'], article_data['content'], CATEGORIES[category], image_id, auth_header)
        if new_post:
            await update.message.reply_text(f"Bài viết đã được đăng: {new_post.get('link')}")
        else:
            await update.message.reply_text("Có lỗi xảy ra khi đăng bài viết.")
    else:
        await update.message.reply_text("Danh mục không hợp lệ. Vui lòng chọn lại.")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection))
    application.run_polling()

if __name__ == '__main__':
    main()
