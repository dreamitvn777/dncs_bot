import logging
import requests
from telegram.ext import Updater, MessageHandler, Filters
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

# 3. Phân tích bài viết từ URL
def extract_article_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi khi lấy nội dung từ URL: {e}")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else "Không có tiêu đề"
    paragraphs = soup.find_all('p')
    article_content = '\n'.join([p.get_text() for p in paragraphs[:5]])  # Giới hạn 5 đoạn đầu
    
    images = soup.find_all('img')
    image_urls = [img.get('src') for img in images[:3]]  # Lấy tối đa 3 ảnh
    
    if not article_content:
        logging.warning("Không tìm thấy nội dung cho bài viết từ URL.")
    
    return {
        'title': title,
        'content': article_content,
        'image_urls': image_urls
    }

# 4. Đăng hình ảnh lên WordPress
def upload_image_to_wordpress(image_url):
    try:
        image_data = requests.get(image_url).content
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi khi tải hình ảnh từ URL: {e}")
        return None
    
    headers = auth_header.copy()
    headers.update({
        'Content-Disposition': f'attachment; filename={image_url.split("/")[-1]}',
        'Content-Type': 'image/jpeg'
    })
    try:
        response = requests.post(f'{wordpress_url}/wp-json/wp/v2/media', headers=headers, data=image_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi khi tải hình ảnh lên WordPress: {e}")
        return None
    
    return response.json().get('id')

# 5. Đăng bài viết lên WordPress
def create_wordpress_post(title, content, image_id=None):
    post_data = {
        'title': title,
        'content': content,
        'status': 'publish'
    }
    
    if image_id:
        post_data['featured_media'] = image_id
    
    try:
        response = requests.post(f'{wordpress_url}/wp-json/wp/v2/posts', headers=auth_header, json=post_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Lỗi khi đăng bài lên WordPress: {e}")
        return None
    
    return response.json()

# 6. Xử lý tin nhắn Telegram
def handle_message(update, context):
    url = update.message.text
    if url.startswith('http'):
        article_data = extract_article_content(url)
        
        if not article_data:
            update.message.reply_text("Không thể phân tích nội dung từ URL. Vui lòng kiểm tra lại.")
            return
        
        # Đăng ảnh đầu tiên lên WordPress nếu có
        image_id = None
        if article_data['image_urls']:
            image_id = upload_image_to_wordpress(article_data['image_urls'][0])
            if not image_id:
                update.message.reply_text("Không thể tải ảnh lên WordPress.")
        
        # Đăng bài lên WordPress
        new_post = create_wordpress_post(article_data['title'], article_data['content'], image_id)
        if new_post:
            update.message.reply_text(f"Bài viết đã được đăng: {new_post.get('link')}")
        else:
            update.message.reply_text("Có lỗi xảy ra khi đăng bài viết.")
    else:
        update.message.reply_text("Vui lòng gửi một URL hợp lệ.")

# 7. Khởi động bot Telegram
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
