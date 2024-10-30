import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

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
def post_facebook(page_id, message, access_token):
    url = f'https://graph.facebook.com/v12.0/{page_id}/feed'
    payload = {
        'message': message,
        'access_token': access_token
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("Đăng bài thành công!")
        return response.json().get('id')  # Trả về ID bài viết
    else:
        print("Lỗi khi đăng bài:", response.json())
        return None

# Hàm xử lý khi nhận URL bài viết từ người dùng
async def handle_facebook_post(update: Update, context: CallbackContext):
    post_url = update.message.text
    await update.message.reply_text('Đang lấy nội dung từ link...')

    # Lấy giá trị từ biến môi trường
    page_id = os.getenv('PAGE_ID')
    access_token = os.getenv('ACCESS_TOKEN')

    # Lấy nội dung bài viết từ link
    post_content = get_facebook_post_content(post_url)

    if post_content:
        # Đăng bài lên Fanpage
        post_id = post_facebook(page_id, post_content, access_token)
        if post_id:
            await update.message.reply_text(f'Đã đăng bài thành công! ID bài viết: {post_id}')
        else:
            await update.message.reply_text('Có lỗi xảy ra khi đăng bài.')
    else:
        await update.message.reply_text('Không thể lấy nội dung từ link đã cho.')

# Hàm bắt đầu bot
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Xin chào! Gửi cho tôi link của bài viết Facebook bạn muốn đăng.')

# Hàm chính
def main():
    # Lấy token từ biến môi trường
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    # Khởi tạo bot
    application = Application.builder().token(telegram_bot_token).build()

    # Đăng ký các handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_facebook_post))

    # Bắt đầu bot
    application.run_polling()

if __name__ == '__main__':
    main()
