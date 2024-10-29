import os
import openai
import requests
import json
import random
import logging
import base64
import httpx  # Thêm thư viện httpx
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Tải các biến môi trường từ file .env
load_dotenv()
# Lấy các thông tin từ file .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
wordpress_url = os.getenv("WORDPRESS_URL")
AUTHORS = json.loads(os.getenv("AUTHORS"))

# Tải danh sách danh mục từ JSON
CATEGORIES = json.loads(os.getenv("CATEGORIES"))

# Thiết lập API key cho OpenAI
openai.api_key = OPENAI_API_KEY


# Hàm sử dụng OpenAI để viết lại nội dung
def rewrite_content_with_openai(content):
    try:
        chat_completion = client.chat.completions.create(
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
        # Lấy nội dung chính xác từ các thẻ <p> mà không bao gồm liên kết ẩn
        content = ''.join([str(p) for p in soup.find_all('p') if not p.find_parent('footer') and 'liên quan' not in p.text.lower()])

        # Lấy URL ảnh
        image_tags = soup.find_all('img')
        image_urls = [img['src'] for img in image_tags if 'src' in img.attrs]
        
        # Viết lại nội dung bằng OpenAI
        rewritten_content = rewrite_content_with_openai(content)
        
        return {"title": title, "content": rewritten_content, "image_urls": image_urls}
    except Exception as e:
        logging.error(f"Lỗi khi phân tích nội dung từ URL: {e}")
        return None


# Hàm tải ảnh lên WordPress
def upload_image_to_wordpress(image_path, wordpress_url, wp_username, wp_password):
    # Đọc tệp ảnh
    with open(image_path, "rb") as image_file:
        # Đọc ảnh dưới dạng nhị phân
        image_data = image_file.read()

    # Mã hóa ảnh sang base64
    encoded_image = base64.b64encode(image_data).decode('utf-8')

    # Tạo payload để gửi lên WordPress
    data = {
        'file': encoded_image,
        'title': 'My Image Title',
        'alt_text': 'Description of the image',
        'post_id': 0  # Bạn có thể thay đổi nếu bạn muốn gắn ảnh vào một bài viết cụ thể
    }

    # Tạo URL cho API tải ảnh lên
    upload_url = f"{wordpress_url}/wp-json/wp/v2/media"

    # Gửi yêu cầu POST
    response = httpx.post(
        upload_url,
        headers={
            'Authorization': f'Basic {base64.b64encode(f"{wp_username}:{wp_password}".encode()).decode()}',
            'Content-Type': 'application/json'
        },
        json=data
    )

    if response.status_code == 201:
        logging.info("Ảnh đã được tải lên thành công!")
        return response.json()  # Trả về thông tin về ảnh đã tải lên
    else:
        logging.error(f"Lỗi khi tải ảnh lên: {response.text}")
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

# Hàm gửi yêu cầu chọn danh mục bài viết
async def send_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(cat, callback_data=cat) for cat in CATEGORIES.keys()]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Vui lòng chọn danh mục:', reply_markup=reply_markup)

# Hàm xử lý khi người dùng chọn danh mục
async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_name = query.data
    context.user_data['selected_category'] = category_name
    await query.edit_message_text(text=f"Bạn đã chọn danh mục: {category_name}. Vui lòng gửi URL bài viết.")

# Hàm xử lý khi nhận URL bài viết từ người dùng
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if url.startswith('http'):
        article_data = await extract_article_content(url)
        
        if not article_data:
            await update.message.reply_text("Không thể phân tích nội dung từ URL.")
            return

        if 'selected_category' not in context.user_data:
            await update.message.reply_text("Vui lòng chọn danh mục trước khi gửi URL.")
            return

        # Chọn ngẫu nhiên tài khoản tác giả
        author = random.choice(AUTHORS)
        wp_user = author["username"]
        wp_password = author["password"]
        
        category_name = context.user_data['selected_category']
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

# Hàm khởi chạy bot Telegram
def main():
    logging.basicConfig(level=logging.INFO)
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', send_category_selection))
    application.add_handler(CallbackQueryHandler(handle_category_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
