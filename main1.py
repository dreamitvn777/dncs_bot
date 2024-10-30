from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os
import telebot
from dotenv import load_dotenv
from dangbai import dang_bai  # Giả sử bạn có hàm dang_bai trong dangbai.py
from danlai import dan_lai    # Giả sử bạn có hàm dan_lai trong danlai.py
from fb1 import post_facebook   # Giả sử bạn có hàm post_facebook trong fb.py

load_dotenv()  # Tải biến môi trường từ file .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['dangbai'])
def handle_dangbai(message):
    # Gọi hàm để đăng bài
    result = dang_bai(message.text)
    bot.reply_to(message, result)

@bot.message_handler(commands=['danlai'])
def handle_danlai(message):
    # Gọi hàm để dẫn lại
    result = dan_lai(message.text)
    bot.reply_to(message, result)

@bot.message_handler(commands=['postfb'])
def handle_postfb(message):
    # Gọi hàm để post lên Facebook
    result = post_facebook(message.text)
    bot.reply_to(message, result)

# Chạy bot
bot.polling()
