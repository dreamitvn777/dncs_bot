import os
import json
import requests
import random
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()  # Tải các biến môi trường từ file .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WORDPRESS_URL = os.getenv("WORDPRESS_URL")
AUTHORS = json.loads(os.getenv("AUTHORS"))
CATEGORIES = json.loads(os.getenv("CATEGORIES"))

# Thiết lập API key cho OpenAI
openai.api_key = OPENAI_API_KEY

# Function to rewrite content using OpenAI
def rewrite_content_with_openai(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Rewrite the content for clarity without changing its meaning."},
                {"role": "user", "content": content}
            ]
        )
        rewritten_content = response.choices[0].message['content'].strip()
        return rewritten_content
    except Exception as e:
        print("Lỗi khi viết lại nội dung với OpenAI:", e)
        return content

# Function to upload an image to WordPress
def upload_image_to_wordpress(image_path, headers):
    with open(image_path, 'rb') as img:
        media_endpoint = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
        headers.update({'Content-Type': 'image/jpeg'})
        response = requests.post(media_endpoint, headers=headers, data=img)
        
        if response.status_code == 201:
            return response.json()['id']  # Image ID to use as featured_media
        else:
            print("Failed to upload image")
            return None

# Function to post an article to WordPress
def post_to_wordpress(title, content, category_id, tags, author, image_path=None):
    headers = {
        'Authorization': f'Basic {author["username"]}:{author["password"]}'
    }
    
    # Optional: Upload image as thumbnail
    image_id = upload_image_to_wordpress(image_path, headers) if image_path else None
    
    # Prepare the post data
    post_data = {
        'title': title,
        'content': content,
        'categories': [category_id],
        'status': 'publish',
        'tags': tags,
        'featured_media': image_id,  # ID của ảnh đại diện nếu có
        'author': author["username"]
    }
    
    # Send the post request
    response = requests.post(f"{WORDPRESS_URL}/wp-json/wp/v2/posts", headers=headers, json=post_data)
    if response.status_code == 201:
        return "Bài viết đã được đăng thành công!"
    else:
        return f"Có lỗi xảy ra khi đăng bài: {response.json()}"

# Hàm chính để đăng bài
def dang_bai(message_text):
    try:
        # Tách thông tin từ tin nhắn
        parts = message_text.split('\n')
        title = parts[0]  # Tiêu đề bài viết là dòng đầu tiên
        content = '\n'.join(parts[1:])  # Nội dung bài viết từ dòng thứ hai trở đi
        
        # Chọn danh mục ngẫu nhiên từ danh sách
        category_id = random.choice(list(CATEGORIES.values()))

        # Nhập hình ảnh và tags (có thể tùy chỉnh cách nhập từ tin nhắn)
        image_path = None  # Có thể lấy từ tin nhắn nếu muốn
        tags = []  # Có thể lấy từ tin nhắn nếu muốn

        # Viết lại nội dung với OpenAI
        rewritten_content = rewrite_content_with_openai(content)

        # Ngẫu nhiên chọn tác giả
        author = random.choice(AUTHORS)

        # Đăng bài lên WordPress
        result = post_to_wordpress(title, rewritten_content, category_id, tags, author, image_path)
        return result
    except Exception as e:
        return f"Có lỗi xảy ra: {str(e)}"
