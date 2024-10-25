import logging
import requests
from telegram.ext import Updater, MessageHandler, filters  # Sử dụng filters
from bs4 import BeautifulSoup
import openai
import base64

# 1. Thiết lập OpenAI và Telegram token
openai.api_key = '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'
TELEGRAM_TOKEN = '7846872870:AAEclA89Hy3i84FqPuh0ozFaHp4wFWLclFg'

# 2. Phân tích bài viết từ URL
def extract_article_content(url):
    response = requests.get(url)
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
def analyze_with_gpt(article_content):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Phân tích nội dung sau: {article_content}",
        max_tokens=200
    )
    return response.choices[0].text.strip()

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
    response = requests.post(f'{wordpress_url}/wp-json/wp/v2/posts', headers=headers, json=post_data)
    return response.json()

# 5. Xử lý tin nhắn Telegram
def handle_message(update, context):
    url = update.message.text
    if url.startswith('http'):
        article_data = extract_article_content(url)
        gpt_analysis = analyze_with_gpt(article_data['content'])
        
        wordpress_url = 'https://doanhnghiepchinhsach.vn/'
        wp_user = 'pv01'
        wp_password = 'cK3UqQ5MhNt0fGq0mjiDpB4C'
        
        new_post = create_wordpress_post(article_data['title'], gpt_analysis, wordpress_url, wp_user, wp_password)
        update.message.reply_text(f"Bài viết đã được đăng: {new_post.get('link')}")
    else:
        update.message.reply_text("Vui lòng gửi một URL hợp lệ.")

# 6. Khởi động bot Telegram
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
