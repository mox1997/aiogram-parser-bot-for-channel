from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import json
import os
from aiogram import Router, F

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
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
        f" чтобы быть в центре новостей. "
        f"Так же вы можете написать пожелания или отзывы нажав на кнопку оставить отзыв!",
        
        parse_mode="HTML"
    )



# Создаем новый класс состояния для отзывов
class FeedbackState(StatesGroup):
    waiting_for_feedback = State()

# Путь к файлу для хранения отзывов
FEEDBACK_FILE = "feedback.json"

def save_feedback(user_id,username, feedback):

    if os.path.exists(FEEDBACK_FILE) and os.path.getsize(FEEDBACK_FILE) > 0:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as file:
            feedback_list = json.load(file)
    else:
        feedback_list = []

    # Добавляем отзыв с ID пользователя
    feedback_entry = {
        "user_id": user_id,
        "username": username,
        "feedback": feedback
    }
    feedback_list.append(feedback_entry)

    with open(FEEDBACK_FILE, "w", encoding="utf-8") as file:
        json.dump(feedback_list, file, ensure_ascii=False, indent=4)

# Команда для начала отправки отзыва
@user_router.message(Command("feedback"))
async def feedback_command(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, напишите ваш отзыв:")
    await state.set_state(FeedbackState.waiting_for_feedback)

@user_router.message(F.text, FeedbackState.waiting_for_feedback)
async def receive_feedback(message: Message, state: FSMContext):
    feedback = message.text.strip()
    user_id = message.from_user.id 
    username = message.from_user.username  

    # Если имя пользователя отсутствует, используем ID
    if username is not None:
        username = f"@{username}"
    else:
        username = f"ID: {user_id}"

    # Сохраняем отзыв в файл
    save_feedback(user_id,username, feedback)
    print("Получен отзыв!")
    await message.answer("Спасибо за ваш отзыв!")
    await state.clear()  # Очищаем состояние после получения отзыва

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
