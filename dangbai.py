import os
import json
import requests
import random
from dotenv import load_dotenv
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Tải biến môi trường từ file .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WORDPRESS_URL = os.getenv("WORDPRESS_URL")
AUTHORS = json.loads(os.getenv("AUTHORS"))
CATEGORIES = json.loads(os.getenv("CATEGORIES"))

# Thiết lập API key cho OpenAI
openai.api_key = OPENAI_API_KEY

# Hàm viết lại nội dung bằng OpenAI
def rewrite_content_with_openai(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Rewrite the content for clarity without changing its meaning."},
                {"role": "user", "content": content}
            ]
        )
        rewritten_content = response.choices[0].message['content'].strip()
        return rewritten_content
    except Exception as e:
        print("Lỗi khi viết lại nội dung với OpenAI:", e)
        return content

# Hàm tải ảnh lên WordPress
def upload_image_to_wordpress(image_path, headers):
    with open(image_path, 'rb') as img:
        media_endpoint = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
        headers.update({'Content-Type': 'image/jpeg'})
        response = requests.post(media_endpoint, headers=headers, data=img)
        
        if response.status_code == 201:
            return response.json()['id']  # ID ảnh để sử dụng làm featured_media
        else:
            print("Failed to upload image")
            return None

# Hàm đăng bài lên WordPress
def post_to_wordpress(title, content, category_id, tags, author, image_path=None):
    headers = {
        'Authorization': f'Basic {author["username"]}:{author["password"]}'
    }
    
    # Tải ảnh lên làm thumbnail nếu có
    image_id = upload_image_to_wordpress(image_path, headers) if image_path else None
    
    # Chuẩn bị dữ liệu bài viết
    post_data = {
        'title': title,
        'content': content,
        'categories': [category_id],
        'status': 'publish',
        'tags': tags,
        'featured_media': image_id,  # ID của ảnh đại diện nếu có
    }
    
    # Gửi yêu cầu đăng bài
    response = requests.post(f"{WORDPRESS_URL}/wp-json/wp/v2/posts", headers=headers, json=post_data)
    if response.status_code == 201:
        return "Bài viết đã được đăng thành công!"
    else:
        return f"Có lỗi xảy ra khi đăng bài: {response.json()}"

# Hàm xử lý khi người dùng bắt đầu đăng bài
async def dang_bai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào! Vui lòng gửi tiêu đề bài viết.")

# Hàm xử lý tiêu đề
async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Vui lòng gửi nội dung bài viết.")

# Hàm xử lý nội dung
async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['content'] = update.message.text
    await update.message.reply_text("Vui lòng gửi từ khóa bài viết (nếu có, dấu '.' để bỏ qua).")

# Hàm xử lý từ khóa
async def handle_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tags_input = update.message.text
    context.user_data['tags'] = tags_input.split(',') if tags_input != '.' else []
    await update.message.reply_text("Vui lòng gửi ảnh đại diện (nếu có, dấu '.' để bỏ qua).")

# Hàm xử lý ảnh
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_path = update.message.text if update.message.text != '.' else None
    context.user_data['image_path'] = image_path
    await update.message.reply_text("Vui lòng gửi sapo (phần mô tả ngắn, nếu có, dấu '.' để bỏ qua).")

# Hàm xử lý sapo
async def handle_sapo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sapo_input = update.message.text
    context.user_data['sapo'] = sapo_input if sapo_input != '.' else None
    
    # Sau khi nhận đủ thông tin, chọn danh mục
    await update.message.reply_text("Vui lòng chọn danh mục bài viết:", reply_markup=create_category_keyboard())

# Hàm tạo bàn phím danh mục
def create_category_keyboard():
    keyboard = [[InlineKeyboardButton(category, callback_data=category) for category in CATEGORIES.keys()]]
    return InlineKeyboardMarkup(keyboard)

# Hàm xử lý khi người dùng chọn danh mục
async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_name = query.data
    context.user_data['selected_category'] = category_name
    await query.edit_message_text(text=f"Bạn đã chọn danh mục: {category_name}. Đang tiến hành đăng bài...")
    
    # Đăng bài lên WordPress
    await post_article(update, context)

# Hàm đăng bài lên WordPress
async def post_article(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = context.user_data.get('title')
    content = context.user_data.get('content')
    tags = context.user_data.get('tags')
    image_path = context.user_data.get('image_path')
    selected_category = context.user_data.get('selected_category')

    # Chọn ngẫu nhiên tài khoản tác giả
    author = random.choice(AUTHORS)
    category_id = CATEGORIES[selected_category]

    # Viết lại nội dung với OpenAI
    rewritten_content = rewrite_content_with_openai(content)

    # Đăng bài
    result = post_to_wordpress(title, rewritten_content, category_id, tags, author, image_path)
    await update.message.reply_text(result)

# Hãy gọi hàm này từ main.py khi người dùng muốn bắt đầu đăng bài
