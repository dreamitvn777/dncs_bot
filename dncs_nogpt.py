import requests
from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackContext
from bs4 import BeautifulSoup
import json
import random
import base64

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = '7846872870:AAEclA89Hy3i84FqPuh0ozFaHp4wFWLclFg'

# WordPress URL
WP_URL = "https://doanhnghiepchinhsach.vn/wp-json/wp/v2/"

# Danh sách tài khoản tác giả WordPress
WP_ACCOUNTS = [
    {"username": "pv01", "password": "CGPP iFrW sC6w N4o1 lM1a Temy"},
    {"username": "dncs_user", "password": "lS6s cUHU a5Fr PXfa 2Krl cCxY"},
    {"username": "dreamitvn", "password": "waxA US8m 3XtO anbm Kc1x w4TT"}
]

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

def get_random_wp_token():
    """Chọn ngẫu nhiên một tài khoản WordPress và trả về mã token xác thực"""
    account = random.choice(WP_ACCOUNTS)
    wp_token = base64.b64encode(f"{account['username']}:{account['password']}".encode()).decode("utf-8")
    return wp_token

def fetch_article_data(url):
    """Lấy và phân tích nội dung bài viết từ URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "Không có tiêu đề"
        content = "\n".join([p.get_text() for p in soup.find_all("p")])
        image_url = soup.find("img")["src"] if soup.find("img") else None
        return title, content, image_url
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu bài viết: {e}")
        return None, None, None

def upload_image_to_wordpress(image_url):
    """Tải lên hình ảnh lên thư viện phương tiện WordPress"""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        headers = {"Authorization": f"Basic {get_random_wp_token()}"}
        files = {
            "file": (image_url.split("/")[-1], response.content),
            "Content-Disposition": "attachment; filename=" + image_url.split("/")[-1]
        }
        res = requests.post(f"{WP_URL}media", headers=headers, files=files)
        res.raise_for_status()
        media_id = res.json().get("id")
        return media_id
    except Exception as e:
        print(f"Lỗi khi tải lên hình ảnh: {e}")
        return None

def post_to_wordpress(title, content, category_id, image_id=None):
    """Đăng nội dung lên WordPress với danh mục và hình ảnh đã chọn"""
    headers = {
        "Authorization": f"Basic {get_random_wp_token()}",
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
        print("Đã đăng bài thành công.")
    except Exception as e:
        print(f"Lỗi khi đăng bài lên WordPress: {e}")

def handle_message(update: Update, context: CallbackContext):
    """Xử lý các tin nhắn Telegram và đăng bài lên WordPress"""
    chat_id = update.effective_chat.id
    if update.message.text.startswith("http"):
        url = update.message.text
        title, content, image_url = fetch_article_data(url)
        
        if not title or not content:
            context.bot.send_message(chat_id, "Lỗi khi lấy nội dung từ liên kết.")
            return

        # Hiển thị danh sách danh mục để người dùng chọn
        buttons = [[category] for category in CATEGORIES.keys()]
        context.bot.send_message(chat_id, "Vui lòng chọn danh mục:", reply_markup=ReplyKeyboardMarkup(buttons))

        def category_selected(update, context):
            category = update.message.text
            category_id = CATEGORIES.get(category)

            if category_id is None:
                context.bot.send_message(chat_id, "Danh mục không hợp lệ.")
                return

            image_id = upload_image_to_wordpress(image_url) if image_url else None
            post_to_wordpress(title, content, category_id, image_id)
            context.bot.send_message(chat_id, "Đã đăng bài thành công.")

        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, category_selected))

    else:
        context.bot.send_message(chat_id, "Vui lòng gửi một URL hợp lệ.")

# Thiết lập Telegram bot
updater = Updater(TELEGRAM_BOT_TOKEN)
dispatcher = updater.dispatcher

# Handlers cho các lệnh và tin nhắn
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Khởi động bot
updater.start_polling()
updater.idle()
