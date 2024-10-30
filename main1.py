from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import json
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # Dùng để lấy nội dung từ URL

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WORDPRESS_URL = os.getenv("WORDPRESS_URL")
AUTHORS = json.loads(os.getenv("AUTHORS"))
CATEGORIES = json.loads(os.getenv("CATEGORIES"))

# Function to handle 'start' command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Đăng bài", callback_data='post_article')],
        [InlineKeyboardButton("Dẫn lại", callback_data='repost_article')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Chọn một chức năng:", reply_markup=reply_markup)

# Function to handle the callback query
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'post_article':
        await choose_category(update, context)
    elif query.data == 'repost_article':
        await update.callback_query.message.reply_text("Gửi URL của bài viết cần dẫn lại:")

# Function to send categories as inline buttons
async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(cat, callback_data=f'cat_{id}')] for cat, id in CATEGORIES.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Chọn một danh mục:", reply_markup=reply_markup)

# Function to handle chosen category and ask for article details
async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['category_id'] = query.data.split('_')[1]  # Save category ID
    await query.message.reply_text("Gửi tiêu đề của bài viết:")

# Handlers for title, content, and thumbnail image
async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Gửi nội dung bài viết:")

async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['content'] = update.message.text
    await update.message.reply_text("Gửi ảnh để làm ảnh thu nhỏ:")

async def handle_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_data = requests.get(photo_file.file_path).content  # Download the photo data
    context.user_data['thumbnail'] = photo_data
    await update.message.reply_text("Đang đăng bài lên WordPress...")
    await post_to_wordpress(update, context)

# Function to post the collected data to WordPress
async def post_to_wordpress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = context.user_data['title']
    content = context.user_data['content']
    category_id = context.user_data['category_id']
    thumbnail = context.user_data['thumbnail']

    # Prepare headers and data for WordPress
    wp_user = AUTHORS[0]["username"]
    wp_pass = AUTHORS[0]["password"]
    headers = {
        'Authorization': f'Basic {wp_user}:{wp_pass}'
    }
    
    # Upload image as thumbnail
    image_id = upload_image_to_wordpress(thumbnail, headers)
    
    # Prepare post data
    post_data = {
        'title': title,
        'content': content,
        'categories': category_id,
        'status': 'publish',
        'featured_media': image_id  # Image ID for featured image
    }

    # Send post request to WordPress
    response = requests.post(f"{WORDPRESS_URL}/wp-json/wp/v2/posts", headers=headers, json=post_data)
    if response.status_code == 201:
        await update.message.reply_text("Bài viết đã được đăng thành công!")
    else:
        await update.message.reply_text("Có lỗi xảy ra khi đăng bài.")

# Image upload function to WordPress
def upload_image_to_wordpress(image_data, headers):
    media_endpoint = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
    headers.update({'Content-Type': 'image/jpeg'})
    response = requests.post(media_endpoint, headers=headers, data=image_data)
    if response.status_code == 201:
        return response.json()['id']  # Image ID used as featured_media in the post
    else:
        raise Exception("Failed to upload image")

# Function to extract and repost an article from a URL
async def repost_article(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    article_data = extract_article_content(url)

    if article_data:
        title = article_data['title']
        content = article_data['content']
        image_url = article_data['image_urls'][0] if article_data['image_urls'] else None

        # Download thumbnail if available
        thumbnail = requests.get(image_url).content if image_url else None
        image_id = upload_image_to_wordpress(thumbnail, headers) if thumbnail else None

        post_data = {
            'title': title,
            'content': content,
            'categories': CATEGORIES.get("Tin trong nước", 1),  # Default category
            'status': 'publish',
            'featured_media': image_id if image_id else None
        }

        response = requests.post(f"{WORDPRESS_URL}/wp-json/wp/v2/posts", headers=headers, json=post_data)
        if response.status_code == 201:
            await update.message.reply_text("Bài viết dẫn lại đã đăng thành công!")
        else:
            await update.message.reply_text("Có lỗi xảy ra khi dẫn lại bài.")

# Function to extract article content from URL
def extract_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else "Không có tiêu đề"
        paragraphs = [p.get_text() for p in soup.find_all('p') if 'liên quan' not in p.get_text().lower()]
        content = '\n'.join(paragraphs)
        
        image_tags = soup.find_all('img')
        image_urls = [img['src'] for img in image_tags if 'src' in img.attrs]

        return {"title": title, "content": content, "image_urls": image_urls}
    except Exception as e:
        print(f"Error extracting content: {e}")
        return None

# Main application setup
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CallbackQueryHandler(handle_category_selection, pattern="^cat_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_content))
app.add_handler(MessageHandler(filters.PHOTO, handle_thumbnail))
app.add_handler(MessageHandler(filters.TEXT, repost_article))  # For reposting

app.run_polling()
