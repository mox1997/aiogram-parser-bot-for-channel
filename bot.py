from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from configs.config import BOT_TOKEN
from admin_handlers import admin_router
from user_handlers import user_router

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())

async def setup_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="admin", description="Админская панель"),
        BotCommand(command="feedback", description="Оставить отзыв"),
    ]
    await bot.set_my_commands(commands)

async def main():
    await setup_commands(bot)
    dp.include_router(user_router)  # Пользовательские команды
    dp.include_router(admin_router)  # Админские команды

    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
