import os
import openai
import requests
import json
import random
import logging
import base64
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes
from urllib.parse import urljoin

# Tải các biến môi trường từ file .env
load_dotenv()

# Lấy các thông tin từ file .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
wordpress_url = os.getenv("WORDPRESS_URL")
AUTHORS = json.loads(os.getenv("AUTHORS"))
CATEGORIES = json.loads(os.getenv("CATEGORIES"))

# Thiết lập API key cho OpenAI
openai.api_key = OPENAI_API_KEY

# Hàm sử dụng OpenAI để viết lại nội dung
def rewrite_content_with_openai(content):
    try:
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that rewrites content for clarity without changing the meaning."},
                {"role": "user", "content": f"Rewrite the following content to improve clarity without changing its meaning:\n\n{content}"}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        return chat_completion['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Lỗi khi viết lại nội dung bằng OpenAI: {e}")
        return content

# Hàm lấy nội dung bài viết từ URL
async def extract_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else "Không có tiêu đề"
        paragraphs = []
        for p in soup.find_all('p'):
            if not p.find_parent('footer') and 'liên quan' not in p.text.lower():
                for a in p.find_all('a'):
                    a.decompose()
                paragraphs.append(str(p))
        
        content = ''.join(paragraphs)

        image_tags = soup.find_all('img')
        image_urls = [urljoin(url, img['src']) for img in image_tags if 'src' in img.attrs]
        
        rewritten_content = rewrite_content_with_openai(content)
        
        return {"title": title, "content": rewritten_content, "image_urls": image_urls}
    except Exception as e:
        logging.error(f"Lỗi khi phân tích nội dung từ URL: {e}")
        return None

# Hàm tải ảnh lên WordPress
def upload_image_to_wordpress(image_url, wordpress_url, wp_username, wp_password):
    try:
        image_data = requests.get(image_url).content
        file_name = image_url.split('/')[-1]
        files = {'file': (file_name, image_data, 'image/jpeg')}
        
        auth_header = {
            'Authorization': 'Basic ' + base64.b64encode(f"{wp_username}:{wp_password}".encode()).decode('utf-8'),
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

# Hàm tạo bài viết mới trên WordPress
def create_wordpress_post(title, content, category_id, image_id=None, wp_user=None, wp_password=None):
    try:
        auth_header = {
            'Authorization': 'Basic ' + base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode('utf-8'),
            'Content-Type': 'application/json'
        }
        
        data = {
            'title': title,
            'content': content,
            'status': 'pending',
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

# Hàm dan_lai để xử lý nội dung bài viết
async def dan_lai(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    article_data = await extract_article_content(url)
    
    if not article_data:
        await update.message.reply_text("Không thể phân tích nội dung từ URL.")
        return

    if 'selected_category' not in context.user_data:
        await update.message.reply_text("Vui lòng chọn danh mục trước khi gửi URL.")
        return

    author = random.choice(AUTHORS)
    wp_user = author["username"]
    wp_password = author["password"]
    
    category_name = context.user_data['selected_category']
    category_id = CATEGORIES[category_name]

    image_id = None
    if article_data['image_urls']:
        image_id = upload_image_to_wordpress(article_data['image_urls'][0], wordpress_url, wp_user, wp_password)
        if not image_id:
            await update.message.reply_text("Không thể tải ảnh lên WordPress.")
    
    new_post = create_wordpress_post(article_data['title'], article_data['content'], category_id, image_id, wp_user, wp_password)
    if new_post:
        await update.message.reply_text(f"Bài viết đã được đăng: {new_post.get('link')}")
    else:
        await update.message.reply_text("Có lỗi xảy ra khi đăng bài viết.")
