from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

# Создаем роутер для пользовательских хэндлеров
user_router = Router()

@user_router.message(Command("start"))
async def start_command(message: Message):
    """
    Хэндлер для команды /start.
    """
    channel_link= "https://t.me/dv_ecological_commission"
    await message.answer(
        f"Добро пожаловать! Этот бот помогает отслеживать экособытия и новости. "
        f"Вы можете подписаться на "
        f'<a href="{channel_link}">канал,</a>'
        f" чтобы быть в центре новостей. ",
        
        parse_mode="HTML"
    )

@user_router.message(Command("help"))
async def help_command(message: Message):
    """
    Хэндлер для команды /help.
    """
    await message.answer(
        "Список доступных команд:\n"
        "/start - Начать работу с ботом\n"
        "/help - Получить помощь\n"
    )
