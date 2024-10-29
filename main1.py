import os
import requests
import json
import random
import logging
import base64
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from urllib.parse import urljoin

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
wordpress_url = os.getenv("WORDPRESS_URL")
AUTHORS = json.loads(os.getenv("AUTHORS"))

# Load categories from JSON environment variable
CATEGORIES = json.loads(os.getenv("CATEGORIES"))

logging.basicConfig(level=logging.INFO)

# Function to rewrite content using OpenAI (if needed)
def rewrite_content_with_openai(content):
    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that rewrites content for clarity without changing the meaning."},
                {"role": "user", "content": f"Rewrite the following content:\n\n{content}"}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        logging.error(f"OpenAI rewrite error: {e}")
        return content

# Function to extract article content from URL
async def extract_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string if soup.title else "Untitled"
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
        logging.error(f"Content extraction error: {e}")
        return None

# Function to upload image to WordPress
def upload_image_to_wordpress(image_url, wp_user, wp_password):
    try:
        image_data = requests.get(image_url).content
        file_name = image_url.split('/')[-1]
        files = {'file': (file_name, image_data, 'image/jpeg')}
        auth = base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode()

        headers = {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json'
        }

        response = requests.post(f"{wordpress_url}/wp-json/wp/v2/media", headers=headers, files=files)
        if response.ok:
            return response.json().get('id')
        else:
            logging.error(f"Image upload failed: {response.json()}")
            return None
    except Exception as e:
        logging.error(f"Image upload error: {e}")
        return None

# Function to create a new post on WordPress
def create_wordpress_post(title, content, category_id, image_id=None, wp_user=None, wp_password=None):
    try:
        auth = base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
        data = {'title': title, 'content': content, 'status': 'publish', 'categories': [category_id]}
        if image_id:
            data['featured_media'] = image_id

        response = requests.post(f"{wordpress_url}/wp-json/wp/v2/posts", headers=headers, json=data)
        if response.ok:
            return response.json()
        else:
            logging.error(f"Post creation failed: {response.json()}")
            return None
    except Exception as e:
        logging.error(f"Post creation error: {e}")
        return None

# Function to send category selection message
async def send_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(cat, callback_data=cat) for cat in CATEGORIES.keys()]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please select a category:', reply_markup=reply_markup)

# Handler for category selection
async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_name = query.data
    context.user_data['selected_category'] = category_name
    await query.edit_message_text(text=f"Category selected: {category_name}. Please send the article URL.")

# Handler for receiving the article URL
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if url.startswith('http'):
        article_data = await extract_article_content(url)
        if not article_data:
            await update.message.reply_text("Unable to parse content from the URL.")
            return

        if 'selected_category' not in context.user_data:
            await update.message.reply_text("Please select a category before sending the URL.")
            return

        author = random.choice(AUTHORS)
        wp_user = author["username"]
        wp_password = author["password"]

        category_name = context.user_data['selected_category']
        category_id = CATEGORIES[category_name]

        image_id = None
        if article_data['image_urls']:
            image_id = upload_image_to_wordpress(article_data['image_urls'][0], wp_user, wp_password)
            if not image_id:
                await update.message.reply_text("Unable to upload the image to WordPress.")

        new_post = create_wordpress_post(article_data['title'], article_data['content'], category_id, image_id, wp_user, wp_password)
        if new_post:
            await update.message.reply_text(f"Post published: {new_post.get('link')}")
        else:
            await update.message.reply_text("Error occurred while publishing the post.")
    else:
        await update.message.reply_text("Please send a valid URL.")

# Main function to start the bot
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler('start', send_category_selection))
    application.add_handler(CallbackQueryHandler(handle_category_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
