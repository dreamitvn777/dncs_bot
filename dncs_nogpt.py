import requests
from bs4 import BeautifulSoup
import openai
import base64
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 1. Thiết lập OpenAI và Telegram token
openai.api_key = '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'
TELEGRAM_TOKEN = '7846872870:AAEclA89Hy3i84FqPuh0ozFaHp4wFWLclFg'

# Thay đổi thông tin WordPress
wordpress_url = 'https://doanhnghiepchinhsach.vn/'
wp_user = 'pv01'
wp_password = '53Tg za3P Xeey FapP jF33 wOKT'

# Thiết lập logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. Lấy nội dung bài viết từ URL
def extract_article_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.title.string if soup.title else "No title"
        paragraphs = soup.find_all('p')
        article_content = '\n'.join([p.get_text() for p in paragraphs[:5]])
        
        return {
            'title': title,
            'content': article_content
        }
    except Exception as e:
        logger.error(f"Error extracting article content: {e}")
        return None

# 3. Phân tích với OpenAI GPT
async def analyze_with_gpt(article_content):
    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Phân tích nội dung sau: {article_content}"}],
            max_tokens=200
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error(f"Error analyzing with GPT: {e}")
        return None

# 4. Đăng bài lên WordPress
def create_wordpress_post(title, content):
    try:
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
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error creating WordPress post: {e}")
        return None

# 5. Xử lý tin nhắn
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    article_data = extract_article_content(url)
    
    if article_data:
        gpt_analysis = await analyze_with_gpt(article_data['content'])
        
        if gpt_analysis:
            new_post = create_wordpress_post(article_data['title'], gpt_analysis)
            
            if new_post:
                await update.message.reply_text(f"Bài đăng mới đã được tạo với ID: {new_post['id']}")
            else:
                await update.message.reply_text("Có lỗi khi tạo bài đăng trên WordPress.")
        else:
            await update.message.reply_text("Có lỗi khi phân tích bài viết với GPT.")
    else:
        await update.message.reply_text("Không thể lấy nội dung từ URL.")

# 6. Hàm main
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Xử lý tin nhắn văn bản
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Chạy bot
    application.run_polling()

if __name__ == '__main__':
    main()
