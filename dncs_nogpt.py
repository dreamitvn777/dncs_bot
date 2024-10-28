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
    """Tải lên hình ảnh lên thư
