import requests
from bs4 import BeautifulSoup
import openai
import logging
import base64
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Cấu hình logging
logging.basicConfig(level=logging.INFO)

# Khai báo biến
TELEGRAM_TOKEN = '7846872870:AAEclA89Hy3i84FqPuh0ozFaHp4wFWLclFg'
wordpress_url = 'https://doanhnghiepchinhsach.vn/'
wp_user = 'dncs_user'
wp_password = 'cK3UqQ5MhNt0fGq0mjiDpB4C'

# 1. Hàm để trích xuất nội dung bài viết
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

# 2. Hàm phân tích với OpenAI GPT
async def analyze_with_gpt(article_content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Phân tích nội dung sau: {article_content}"}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f'Lỗi khi phân tích với GPT: {e}')
        return None

# 3. Hàm đăng bài lên WordPress
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
        if response.status_code == 201:
            logging.info('Bài đăng đã được tạo thành công.')
        else:
            logging.error(f'Lỗi khi tạo bài đăng: {response.status_code} - {response.text}')
        return response.json()
    except Exception as e:
        logging.error(f'Lỗi khi gửi yêu cầu đến WordPress: {e}')
        return None

# 4. Hàm xử lý tin nhắn
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    logging.info(f'Nhận URL: {url}')

    article_data = extract_article_content(url)
    gpt_analysis = await analyze_with_gpt(article_data['content'])

    if gpt_analysis:
        new_post = create_wordpress_post(article_data['title'], gpt_analysis, wordpress_url, wp_user, wp_password)
        update.message.reply_text(f'Đã tạo bài đăng mới: {new_post.get("link", "Không có link")}')
    else:
        update.message.reply_text('Không thể phân tích nội dung bài viết.')

# 5. Hàm main
def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info('Bot đã khởi động và đang lắng nghe tin nhắn...')
    application.run_polling()

if __name__ == "__main__":
    main()
