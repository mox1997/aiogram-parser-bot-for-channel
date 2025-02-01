import json
import os
import re
from aiogram import Router, F
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from parser import parse_news, post_to_channel, scheduled_parsing
from configs.config import CHANNEL_ID
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from configs.config import ADMIN_ID

admin_router = Router()
storage = MemoryStorage()  # Используем память для хранения состояний
FEEDBACK_FILE = "feedback.json"

# FSM для отслеживания состояния
class ManualParsingState(StatesGroup):
    waiting_for_link = State()
    waiting_for_confirmation = State()
    waiting_for_correction = State()

admin_router = Router()
# Глобальные переменные для планировщика
scheduler = AsyncIOScheduler()
scheduler_started = False
# Создаём инлайн-клавиатуру
def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Включить автоматический парсинг", callback_data="enable_auto_parsing"),
            InlineKeyboardButton(text="Выключить автоматический парсинг", callback_data="disable_auto_parsing"),
        ],
        [
            InlineKeyboardButton(text="Выборочный парсинг", callback_data="manual_parsing"),
        ],
        [
            InlineKeyboardButton(text="Показать статус", callback_data="show_status"),
            InlineKeyboardButton(text="Получить отзывы", callback_data="get_feedback"),
        ]
    ])
    return keyboard

# Включение автоматического парсинга
async def enable_auto_parsing(bot: Bot, url: str,state: FSMContext):
    global scheduler, scheduler_started
    if not scheduler_started:
        scheduler.start()
        scheduler_started = True

    scheduler.remove_all_jobs()
    scheduler.add_job(scheduled_parsing, "interval", seconds=3600, kwargs={"bot": bot, "url": url, "state": state})
    print("Автоматический парсинг включён.")

# Выключение автоматического парсинга
async def disable_auto_parsing():
    global scheduler, scheduler_started
    if scheduler_started:
        scheduler.remove_all_jobs()
        scheduler.shutdown()
        scheduler_started = False
        print("Автоматический парсинг выключён.")


# Хэндлер для команды /admin
@admin_router.message(Command("admin"))
async def admin_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Вы не являетесь администратором!")
        return

    await message.answer(
        "Добро пожаловать в админскую панель! Выберите действие:",
        reply_markup=get_admin_keyboard()
    )

@admin_router.callback_query(ManualParsingState.waiting_for_confirmation)
async def confirm_or_edit_or_cancel(callback: CallbackQuery, state: FSMContext, bot: Bot):
   # print(f"DEBUG: callback_data = {callback.data}")
   # print(f"DEBUG: Текущее состояние = {await state.get_state()}")
    action = callback.data
    print(f"Получено callback_data: {action}") 
    data = await state.get_data()
    # Проверяем, есть ли данные
    if "news" not in data:
        await callback.message.answer("Ошибка: данные о новости отсутствуют.")
        await state.clear()  # Очищаем состояние, если данные отсутствуют
        return
    news = data["news"]
    url = data["url"]
    title = re.sub(r'\s+', ' ', news["title"]).strip()  # Заменяем все пробельные символы на один пробел
    content = re.sub(r'\s+', ' ', news["content"]).strip()  # Аналогично для контентаstrip()

    if action == "confirm":
        # Отправляем в канал
        await post_to_channel(bot, title, content, url)
        await callback.message.answer("Новость отправлена в канал!")
        await state.clear()
    elif action == "edit":
        # Уведомление об отправке исправленного текста
        await callback.message.answer(
            "Отправьте исправленный текст в формате:\n\n"
            "<b>Заголовок</b>\n\n<b>Контент</b>",
            parse_mode="HTML"
        )
        await state.set_state(ManualParsingState.waiting_for_correction)
    elif action == "cancel":
        # Завершаем обработку
        await callback.message.answer("Отмена действия. Ничего не было отправлено.")
        await state.clear()  # Сбрасываем состояние FSM
    await callback.answer()


# Ограничьте общий хэндлер, чтобы он не перехватывал все callback-запросы
@admin_router.callback_query()
async def admin_callback_handler(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # Если есть активное состояние, не обрабатываем запрос здесь
    current_state = await state.get_state()
    if current_state is not None:
        print(f"Пропускаем общий хэндлер, текущее состояние: {current_state}")
        return

    action = callback.data

    if action == "enable_parsing":
        await callback.message.answer("Парсинг включен.")
        print(f"Получено callback_data: {action}")
        # Логика включения парсинга
    elif action == "disable_parsing":
        await callback.message.answer("Парсинг выключен.")
        print(f"Получено callback_data: {action}")
    elif action == "enable_auto_parsing":
        await enable_auto_parsing(bot, url="https://ngofeec.com/", state=state)
        await callback.message.answer("Автоматический парсинг включен.")
        print(f"Получено callback_data: {action}")
        # Логика включения парсинга
    elif action == "disable_auto_parsing":
        await disable_auto_parsing()
        await callback.message.answer("Автоматический парсинг выключен.")
        print(f"Получено callback_data: {action}")
        # Логика выключения парсинга
    elif action == "manual_parsing":
        await start_manual_parsing(callback.message, state)
        print(f"Получено callback_data: {action}")
    elif action == "show_status":
        await callback.message.answer("Режим: автоматический")
        print(f"Получено callback_data: {action}")
        # Логика для отображения статуса
    elif action == "get_feedback":
        await send_feedback_to_admin(bot, callback.message.chat.id)
        print(f"Получено callback_data: {action}")
    else:
        await callback.answer("Неизвестная команда.", show_alert=True)
        print(f"Получено callback_data: неизвестная команда")
    
    await callback.answer()

async def send_feedback_to_admin(bot: Bot, chat_id):
    if os.path.exists(FEEDBACK_FILE) and os.path.getsize(FEEDBACK_FILE) > 0:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as file:
            feedback_list = json.load(file)

        if feedback_list:
            feedback_messages = []
            for entry in feedback_list:
                username = entry["username"]  # Используем username вместо user_id
                feedback = entry["feedback"]
                feedback_messages.append(f"Пользователь: {username}\nОтзыв: {feedback}\n")

            # Объединяем все отзывы в одно сообщение
            all_feedback = "\n".join(feedback_messages)
            await bot.send_message(chat_id, f"Отзывы:\n\n{all_feedback}")
        else:
            await bot.send_message(chat_id, "Нет отзывов.")
    else:
        await bot.send_message(chat_id, "Нет отзывов.")

# Команда для начала выборочного парсинга
@admin_router.message(Command("manual_parsing"))
async def start_manual_parsing(message: Message, state: FSMContext):
    
    await message.answer("Отправьте ссылку на новость для парсинга.")
    await state.set_state(ManualParsingState.waiting_for_link)

async def send_auto_parsing_to_admin(bot: Bot, news: dict, url: str,state: FSMContext):
    """
    Отправляет результаты автоматического парсинга админу для подтверждения.
    """
    title = news["title"].strip()
    content = news["content"].strip()
    url=url
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="Редактировать", callback_data="edit"),
            InlineKeyboardButton(text="Отменить", callback_data="cancel")
        ]
    ])
    # Устанавливаем состояние для обработки ответов на кнопки
    await state.set_state(ManualParsingState.waiting_for_confirmation)

    # Отправляем сообщение админу
    await bot.send_message(
        ADMIN_ID,
        f"<b>Автоматически спарсенная новость:</b>\n\n"
        f"<b>Заголовок:</b> {title}\n\n"
        f"<b>Контент:</b> {content}\n\n"
        f"Ссылка: {url}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    # Сохраняем исправленный текст
    news = {"title": title, "content": content}
    await state.update_data(news=news,url=url)

# Получение ссылки от администратора
@admin_router.message(F.text, ManualParsingState.waiting_for_link)
async def receive_link(message: Message, state: FSMContext, bot: Bot):
    url = message.text.strip()
    news = parse_news(url)
    
    if "error" in news:
        await message.answer(f"Ошибка парсинга: {news['error']}")
        await state.clear()
        return

    # Сохраняем данные в состояние
    await state.update_data(news=news, url=url)

    # Отправляем предварительный результат администратору
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="Редактировать", callback_data="edit"),
            InlineKeyboardButton(text="Отменить", callback_data="cancel")
        ]
    ])
    # Очистка заголовка и контента
    title = re.sub(r'\s+', ' ', news["title"]).strip()  # Заменяем все пробельные символы на один пробел
    content = re.sub(r'\s+', ' ', news["content"]).strip()  # Аналогично для контентаstrip()
    await message.answer(
        f"<b>Предварительный результат парсинга:</b>\n\n"
        f"<b>Заголовок:</b> {title}\n\n"
        f"<b>Контент:</b> {content}\n\n"
        f"Ссылка: {url}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ManualParsingState.waiting_for_confirmation)
    print("Состояние установлено: waiting_for_confirmation")

# Обработка исправленного текста
@admin_router.message(F.text, ManualParsingState.waiting_for_correction)
async def receive_correction(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip().split("\n\n", 1)

    if len(text) < 2:
        await message.answer("Некорректный формат. Отправьте текст в формате:\n\n<заголовок>\n\n<контент>")
        return

    title, content = text
    data = await state.get_data()
    url = data["url"]

    # Сохраняем исправленный текст
    news = {"title": title, "content": content}
    await state.update_data(news=news)

    # Спрашиваем подтверждение
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="Редактировать", callback_data="edit"),
            InlineKeyboardButton(text="Отменить", callback_data="cancel")
        ]
    ])
    await message.answer(
        f"<b>Исправленный текст:</b>\n\n"
        f"<b>Заголовок:</b> {title}\n\n"
        f"<b>Контент:</b> {content}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(ManualParsingState.waiting_for_confirmation)

@admin_router.callback_query()
async def debug_all_callbacks(callback: CallbackQuery):
    print(f"DEBUG: Получен callback_data: {callback.data}")
    await callback.answer("Обратный вызов обработан.")
