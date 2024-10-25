import logging
import requests
from telegram.ext import Application, MessageHandler, filters
from bs4 import BeautifulSoup
import openai
import base64
import asyncio

# 1. Thiết lập OpenAI và Telegram token
TELEGRAM_TOKEN = '7846872870:AAEclA89Hy3i84FqPuh0ozFaHp4wFWLclFg'

# Thiết lập logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Phân tích bài viết từ URL
def extract_article_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching article: {e}")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    title = soup.title.string if soup.title else "No title"
    paragraphs = soup.find_all('p')
    article_content = '\n'.join([p.get_text() for p in paragraphs[:5]])  # Giới hạn 5 đoạn đầu
    
    images = soup.find_all('img')
    image_urls = [img.get('src') for img in images[:3]]  # Lấy tối đa 3 ảnh
    
    return {
        'title': title,
        'content': article_content,
        'image_urls': image_urls
    }

# 3. Phân tích với OpenAI GPT

# 4. Đăng bài lên WordPress
def create_wordpress_post(title, content, wordpress_url, wp_user, wp_password):
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode('utf-8'),
        'Content-Type': 'application/json'
    }
    post_data = {
        'title': title,
        'content': content,
        'status': 'publish'
    }
    try:
        response = requests.post(f'{wordpress_url}/wp-json/wp/v2/posts', headers=headers, json=post_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error posting to WordPress: {e}")
        return None

# 5. Xử lý tin nhắn Telegram
async def handle_message(update, context):
    url = update.message.text
    if url.startswith('http'):
        article_data = extract_article_content(url)
        if article_data is None:
            await update.message.reply_text("Không thể lấy nội dung bài viết.")
            return

        gpt_analysis = await analyze_with_gpt(article_data['content'])
        
        wordpress_url = 'https://doanhnghiepchinhsach.vn/'
        wp_user = 'dncs_user'
        wp_password = 'bk0Nw7MBvX)B@blmxsM4zrOI'
        
        new_post = create_wordpress_post(article_data['title'], gpt_analysis, wordpress_url, wp_user, wp_password)
        if new_post is None:
            await update.message.reply_text("Đăng bài lên WordPress không thành công.")
        else:
            await update.message.reply_text(f"Bài viết đã được đăng: {new_post.get('link')}")
    else:
        await update.message.reply_text("Vui lòng gửi một URL hợp lệ.")

# 6. Khởi động bot Telegram
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.run_polling()  # Không cần await ở đây

if __name__ == '__main__':
    main()  # Gọi hàm main mà không cần asyncio.run

