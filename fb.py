import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Tải biến môi trường từ file .env
load_dotenv()

# Hàm lấy nội dung từ link Facebook
def get_facebook_post_content(post_url):
    response = requests.get(post_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        post_content = soup.find('div', {'data-ad-preview': 'message'})
        if post_content:
            return post_content.get_text()
    return None

# Hàm đăng bài lên Fanpage
def post_to_facebook_page(page_id, message, access_token):
    url = f'https://graph.facebook.com/v12.0/{page_id}/feed'
    payload = {
        'message': message,
        'access_token': access_token
    }
    
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        print("Đăng bài thành công!")
        print("ID bài viết:", response.json().get('id'))
    else:
        print("Lỗi khi đăng bài:", response.json())

# Hàm bắt đầu bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Xin chào! Gửi cho tôi link của bài viết Facebook bạn muốn đăng.')

# Hàm xử lý tin nhắn từ người dùng
def handle_message(update: Update, context: CallbackContext) -> None:
    post_url = update.message.text
    update.message.reply_text('Đang lấy nội dung từ link...')

    # Lấy giá trị từ biến môi trường
    page_id = os.getenv('PAGE_ID')
    access_token = os.getenv('ACCESS_TOKEN')

    # Lấy nội dung bài viết từ link
    post_content = get_facebook_post_content(post_url)
    
    if post_content:
        # Đăng bài lên Fanpage
        post_to_facebook_page(page_id, post_content, access_token)
        update.message.reply_text('Đã đăng bài thành công!')
    else:
        update.message.reply_text('Không thể lấy nội dung từ link đã cho.')

# Hàm chính
def main():
    # Lấy token từ biến môi trường
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    # Khởi tạo bot
    updater = Updater(telegram_bot_token)

    # Lấy dispatcher để đăng ký handler
    dispatcher = updater.dispatcher

    # Đăng ký các handler
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Bắt đầu bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
