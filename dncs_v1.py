import requests
import json
import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from bs4 import BeautifulSoup

# WordPress details
wordpress_url = 'https://doanhnghiepchinhsach.vn/wp-json/wp/v2/posts'
wp_user = 'pv01'
wp_application_password = '53Tg za3P Xeey FapP jF33 wOKT'

# Telegram bot token và chat ID
TELEGRAM_TOKEN = '7957341943:AAHnEmoz-IbiGLFmvrGCmWVytpFW9-WZd78'
telegram_chat_id = '-4569179837'  # ID chat của bạn

# Logging setup
logging.basicConfig(level=logging.INFO)

# Telegram bot for logging errors
bot = Bot(token=TELEGRAM_TOKEN)

# Function to send error message via Telegram
def send_error_to_telegram(message):
    bot.send_message(chat_id=telegram_chat_id, text=f"Lỗi: {message}")

# Function to create a WordPress post
def create_wordpress_post(title, content, image_url):
    try:
        # Get image and upload to WordPress
        image_id = upload_image_to_wordpress(image_url)

        # Set post data
        post_data = {
            'title': title,
            'content': content,
            'status': 'publish',
            'featured_media': image_id  # Set featured image
        }

        # Send post request to WordPress API
        response = requests.post(wordpress_url, json=post_data, auth=(wp_user, wp_application_password))

        if response.status_code == 201:
            logging.info(f"Đăng bài thành công: {title}")
        else:
            logging.error(f"Lỗi đăng bài: {response.content}")
            send_error_to_telegram(f"Lỗi đăng bài: {response.content}")
    except Exception as e:
        logging.error(f"Lỗi tạo bài viết: {str(e)}")
        send_error_to_telegram(f"Lỗi tạo bài viết: {str(e)}")

# Function to upload image to WordPress
def upload_image_to_wordpress(image_url):
    try:
        image_data = requests.get(image_url).content
        media_url = f'{wordpress_url}/media'
        media_headers = {'Content-Disposition': f'attachment; filename=image.jpg'}
        media_response = requests.post(media_url, data=image_data, headers=media_headers, auth=(wp_user, wp_application_password))

        if media_response.status_code == 201:
            media_id = media_response.json()['id']
            logging.info(f"Tải ảnh lên thành công, media ID: {media_id}")
            return media_id
        else:
            logging.error(f"Lỗi tải ảnh lên: {media_response.content}")
            send_error_to_telegram(f"Lỗi tải ảnh lên: {media_response.content}")
            return None
    except Exception as e:
        logging.error(f"Lỗi tải ảnh lên WordPress: {str(e)}")
        send_error_to_telegram(f"Lỗi tải ảnh lên WordPress: {str(e)}")
        return None

# Function to handle incoming Telegram messages
async def handle_message(update: Update, context):
    try:
        message = update.message.text
        if message.startswith("http"):
            # Fetch article content
            response = requests.get(message)
            soup = BeautifulSoup(response.content, 'html.parser')

            title = soup.title.string
            content = soup.get_text()

            # Extract first image from article
            image = soup.find('img')
            image_url = image['src'] if image else None

            # Create post on WordPress
            create_wordpress_post(title, content, image_url)
        else:
            update.message.reply_text("Vui lòng gửi link bài viết.")
    except Exception as e:
        logging.error(f"Lỗi xử lý tin nhắn: {str(e)}")
        send_error_to_telegram(f"Lỗi xử lý tin nhắn: {str(e)}")

# Main function to run the bot
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    app.add_handler(message_handler)

    logging.info("Bot đã sẵn sàng.")
    await app.start()
    await app.idle()

# Chạy bot
if __name__ == '__main__':
    try:
        import asyncio
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Lỗi khởi chạy bot: {str(e)}")
        send_error_to_telegram(f"Lỗi khởi chạy bot: {str(e)}")
