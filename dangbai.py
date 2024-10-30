import os
import json
import requests
import random
from dotenv import load_dotenv
import openai

# Load environment variables
# Lấy các thông tin từ file .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WORDPRESS_URL = os.getenv("WORDPRESS_URL")
AUTHORS = json.loads(os.getenv("AUTHORS"))

# Tải danh sách danh mục từ JSON
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
        print("Bài viết đã được đăng thành công!")
    else:
        print("Có lỗi xảy ra khi đăng bài:", response.json())

# Main function to collect data and post
def main():
    print("===== Đăng Bài Lên WordPress =====")
    
    # Choose category
    print("Chọn danh mục bài viết:")
    for idx, (name, cat_id) in enumerate(CATEGORIES.items(), 1):
        print(f"{idx}. {name}")
    
    cat_choice = int(input("Nhập số thứ tự của danh mục: ")) - 1
    category_id = list(CATEGORIES.values())[cat_choice]
    
    # Collect post details
    title = input("Nhập tiêu đề bài viết: ")
    content = input("Nhập nội dung bài viết: ")
    image_path = input("Nhập đường dẫn đến ảnh đại diện (bỏ qua nếu không có): ")
    image_path = image_path if image_path else None
    tags = input("Nhập từ khóa (các từ khóa cách nhau bằng dấu phẩy): ").split(',')
    tags = [tag.strip() for tag in tags]  # Strip whitespace from tags
    
    # Rewrite content with OpenAI
    rewritten_content = rewrite_content_with_openai(content)
    
    # Randomly select an author
    author = random.choice(AUTHORS)
    
    # Post to WordPress
    post_to_wordpress(title, rewritten_content, category_id, tags, author, image_path)

if __name__ == "__main__":
    main()
