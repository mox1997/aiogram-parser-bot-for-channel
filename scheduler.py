from apscheduler.schedulers.asyncio import AsyncIOScheduler
from configs.config import BOT_TOKEN
from aiogram import Bot
from parser import parse_news, post_to_channel

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.start()

def add_job(interval, func, *args, **kwargs):
    scheduler.add_job(func, "interval", seconds=interval, args=args, kwargs=kwargs)

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    
    # Запуск планировщика
    start_scheduler()
    add_job(interval=3600, func=scheduled_parsing, bot=bot, url="https://example.com/news")  # Парсинг каждый час



async def scheduled_parsing(bot, url: str):
    """
    Задача для планировщика: парсинг и отправка новостей в канал.
    
    :param bot: Экземпляр бота для отправки сообщений.
    :param url: URL сайта для парсинга.
    """
    # Парсим новость
    news = parse_news(url)
    
    # Если парсинг успешный, отправляем в канал
    if "error" not in news:
        await post_to_channel(bot, news["title"], news["content"], url)
        print(f"Новость отправлена: {news['title']}")
    else:
        print(f"Ошибка парсинга: {news['error']}")
