import requests
from bs4 import BeautifulSoup
from aiogram import Bot
from configs.config import CHANNEL_ID
from newspaper import Article
def parse_news(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Пробуем найти заголовок и контент с использованием стандартных методов
        title = None
        content = None

        # Пробуем найти заголовок
        title_tag = soup.find(["h1", "h2", "h3"])  # Поддерживаем несколько тегов для заголовка
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Пробуем найти контент
        content_tag = soup.find(["div", "article", "section", "main"])  # Возможные контейнеры для контента
        if content_tag:
            content = content_tag.get_text(strip=True)
            print('Используется beautifulSoup для парсинга')

        # Если не удалось извлечь данные, используем newspaper3k
        if not title or not content:
            print("Используется библиотека newspaper для парсинга")
            article = Article(url)
            article.download()
            article.parse()
            title = article.title if not title else title
            content = article.text if not content else content
        return {"title": title, "content": content}
    except Exception as e:
        return {"error": str(e)}



async def post_to_channel(bot: Bot, title: str, content: str, link: str):
    """
    Отправка спарсенной новости в Telegram канал.
    """
    try:
        message = f"<b>{title}</b>\n\n{content}\n\n<a href='{link}'>Читать далее</a>"
        await bot.send_message(chat_id=CHANNEL_ID, text=message, disable_web_page_preview=False)
    except Exception as e:
        print(f"Ошибка отправки в канал: {e}")
