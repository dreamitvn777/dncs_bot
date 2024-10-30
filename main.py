from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import subprocess  # Dùng để gọi các file bên ngoài
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Function to handle 'start' command and present options
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Đăng bài", callback_data='dang_bai')],
        [InlineKeyboardButton("Dẫn lại", callback_data='dan_lai')],
        [InlineKeyboardButton("Post Fanpage", callback_data='post_fanpage')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Chọn một chức năng:", reply_markup=reply_markup)

# Function to handle the callback query
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Call the respective script based on user selection
    if query.data == 'dang_bai':
        await run_script(update, "dangbai.py", "Đăng bài")
    elif query.data == 'dan_lai':
        await run_script(update, "danlai.py", "Dẫn lại")
    elif query.data == 'post_fanpage':
        await run_script(update, "fb.py", "Đăng lên Fanpage")

# Function to run the specified script and notify user
async def run_script(update: Update, script_name: str, action_name: str):
    await update.callback_query.message.reply_text(f"Đang thực hiện chức năng {action_name}...")
    try:
        # Run the selected script
        subprocess.run(["python3", script_name], check=True)
        await update.callback_query.message.reply_text(f"{action_name} thành công!")
    except subprocess.CalledProcessError:
        await update.callback_query.message.reply_text(f"Có lỗi xảy ra khi {action_name.lower()}.")

# Main application setup
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
