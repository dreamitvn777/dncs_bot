import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

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
        return f"Đăng bài thành công! ID bài viết: {response.json().get('id')}"
    else:
        return f"Lỗi khi đăng bài: {response.json()}"

# Hàm đăng bài từ link Facebook
def postfb(post_url):
    # Lấy giá trị từ biến môi trường
    page_id = os.getenv('PAGE_ID')
    access_token = os.getenv('ACCESS_TOKEN')

    # Lấy nội dung bài viết từ link
    post_content = get_facebook_post_content(post_url)
    
    if post_content:
        # Đăng bài lên Fanpage
        result = post_to_facebook_page(page_id, post_content, access_token)
        return result
    else:
        return 'Không thể lấy nội dung từ link đã cho.'
