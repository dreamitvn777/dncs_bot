import logging
import requests
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from bs4 import BeautifulSoup

# Thiết lập logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Thiết lập thông tin WordPress và Telegram
WORDPRESS_URL = 'https://doanhnghiepchinhsach.vn/wp-json/wp/v2/posts'
WORDPRESS_USERNAME = 'pv01'  # Thay bằng username của bạn
WORDPRESS_APP_PASSWORD = '53Tg za3P Xeey FapP jF33 wOKT'  # Thay bằng mật khẩu ứng dụng của bạn
TELEGRAM_TOKEN = '7957341943:AAHnEmoz-IbiGLFmvrGCmWVytpFW9-WZd78'  # Thay bằng token của bot Telegram
telegram_chat_id = '-4569179837'  # Thay bằng ID chat của bạn

# Tạo đối tượng bot Telegram
bot = Bot(token=TELEGRAM_TOKEN)

# Hàm gửi thông báo lỗi qua Telegram
async def send_error_to_telegram(chat_id, message):
    await bot.send_message(chat_id=chat_id, text=f"Lỗi: {message}")

# Hàm phân tích nội dung từ link
def analyze_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Lấy tiêu đề
        title = soup.title.string if soup.title else "Không có tiêu đề"

        # Lấy nội dung bài viết
        content = soup.get_text(separator="\n")

        # Lấy ảnh thumbnail (có thể thay đổi tùy vào cấu trúc HTML của trang)
        thumbnail_url = soup.find('meta', property='og:image')['content'] if soup.find('meta', property='og:image') else ""

        # Lấy ảnh trong bài viết (giả sử lấy ảnh đầu tiên trong bài)
        images = [img['src'] for img in soup.find_all('img')]
        first_image_url = images[0] if images else ""

        return title, content, thumbnail_url, first_image_url
    except Exception as e:
        logger.error(f"Lỗi phân tích link: {e}")
        return None, None, None, None

# Hàm đăng bài lên WordPress
async def post_to_wordpress(title, content, thumbnail_url, first_image_url):
    post = {
        'title': title,
        'content': content,
        'status': 'publish',
        'featured_media': thumbnail_url  # Cần upload hình ảnh lên WP trước khi sử dụng
    }
    try:
        response = requests.post(
            WORDPRESS_URL,
            json=post,
            auth=(WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD)
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Lỗi đăng bài: {e}")
        await send_error_to_telegram(telegram_chat_id, f"Lỗi đăng bài: {e}")

# Hàm xử lý tin nhắn
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Nhận link từ tin nhắn
        article_url = update.message.text
        
        # Phân tích nội dung từ link
        title, content, thumbnail_url, first_image_url = analyze_link(article_url)

        if title and content:
            await post_to_wordpress(title, content, thumbnail_url, first_image_url)
            await update.message.reply_text("Bài viết đã được đăng thành công!")
        else:
            await update.message.reply_text("Không thể phân tích nội dung từ link.")
    except Exception as e:
        logger.error(f"Lỗi xử lý tin nhắn: {e}")
        await send_error_to_telegram(telegram_chat_id, str(e))

# Hàm main
async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
