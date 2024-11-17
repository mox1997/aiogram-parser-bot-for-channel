import os
from dotenv import load_dotenv


load_dotenv(dotenv_path="configs/conf.env")  # Замените на реальный путь
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # ID админа для панели управления
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Telegram канал для публикации

#print(BOT_TOKEN)
#print(ADMIN_ID)
#print(CHANNEL_ID)