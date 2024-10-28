import requests
from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackContext
from bs4 import BeautifulSoup
import json

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = '7846872870:AAEclA89Hy3i84FqPuh0ozFaHp4wFWLclFg'
# WordPress Credentials
WP_URL = "https://doanhnghiepchinhsach.vn/wp-json/wp/v2/"
WP_USERNAME = "dreamitvn"
WP_PASSWORD = "waxA US8m 3XtO anbm Kc1x w4TT"

# Base64 encoding for WordPress authentication
import base64
wp_token = base64.b64encode(f"{WP_USERNAME}:{WP_PASSWORD}".encode()).decode("utf-8")

# WordPress Category IDs
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

def fetch_article_data(url):
    """Fetch and parse article content from URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "No Title"
        content = "\n".join([p.get_text() for p in soup.find_all("p")])
        image_url = soup.find("img")["src"] if soup.find("img") else None
        return title, content, image_url
    except Exception as e:
        print(f"Error fetching article data: {e}")
        return None, None, None

def upload_image_to_wordpress(image_url):
    """Upload image to WordPress media library"""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        headers = {"Authorization": f"Basic {wp_token}"}
        files = {
            "file": (image_url.split("/")[-1], response.content),
            "Content-Disposition": "attachment; filename=" + image_url.split("/")[-1]
        }
        res = requests.post(f"{WP_URL}media", headers=headers, files=files)
        res.raise_for_status()
        media_id = res.json().get("id")
        return media_id
    except Exception as e:
        print(f"Error uploading image: {e}")
        return None

def post_to_wordpress(title, content, category_id, image_id=None):
    """Post content to WordPress with selected category and image"""
    headers = {
        "Authorization": f"Basic {wp_token}",
        "Content-Type": "application/json"
    }
    data = {
        "title": title,
        "content": content.replace("\n", "<br>"),
        "status": "publish",
        "categories": [category_id]
    }
    if image_id:
        data["featured_media"] = image_id

    try:
        response = requests.post(f"{WP_URL}posts", headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print("Post published successfully.")
    except Exception as e:
        print(f"Error posting to WordPress: {e}")

def handle_message(update: Update, context: CallbackContext):
    """Process incoming Telegram messages and post to WordPress"""
    chat_id = update.effective_chat.id
    if update.message.text.startswith("http"):
        url = update.message.text
        title, content, image_url = fetch_article_data(url)
        
        if not title or not content:
            context.bot.send_message(chat_id, "Error fetching content from the link.")
            return

        # Prompt for category selection
        buttons = [[category] for category in CATEGORIES.keys()]
        context.bot.send_message(chat_id, "Please choose a category:", reply_markup=ReplyKeyboardMarkup(buttons))

        def category_selected(update, context):
            category = update.message.text
            category_id = CATEGORIES.get(category)

            if category_id is None:
                context.bot.send_message(chat_id, "Invalid category selected.")
                return

            image_id = upload_image_to_wordpress(image_url) if image_url else None
            post_to_wordpress(title, content, category_id, image_id)
            context.bot.send_message(chat_id, "Post published successfully.")

        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, category_selected))

    else:
        context.bot.send_message(chat_id, "Please send a valid URL.")

# Telegram bot setup
updater = Updater(TELEGRAM_BOT_TOKEN)
dispatcher = updater.dispatcher

# Command and message handlers
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Start the bot
updater.start_polling()
updater.idle()
