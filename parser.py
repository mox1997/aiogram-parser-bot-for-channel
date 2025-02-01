import json
import os
import requests
from bs4 import BeautifulSoup
from aiogram import Bot
from configs.config import CHANNEL_ID,ADMIN_ID
from newspaper import Article
from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext


PROCESSED_LINKS_FILE = "processed_links.json"

# Загружаем обработанные ссылки из файла
if os.path.exists(PROCESSED_LINKS_FILE):
    with open(PROCESSED_LINKS_FILE, "r") as file:
        processed_links = set(json.load(file))
else:
    processed_links = set()

def save_processed_links():
    with open(PROCESSED_LINKS_FILE, "w") as file:
        json.dump(list(processed_links), file, indent=4)  # Используем indent=4 для читабельности


def parse_news(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Инициализируем переменные title и content
        title = None
        content = None

        # Если не удалось извлечь данные с BeautifulSoup, используем newspaper3k
        print("Используется библиотека newspaper для парсинга")
        article = Article(url)
        article.download()
        article.parse()
        title = article.title if title is None else title  # Используем title из newspaper, если оно не было найдено до этого
        content = article.text if content is None else content  # То же для контента

        # Ограничиваем длину контента до 1000 символов (можно настроить в зависимости от предпочтений)
        max_length = 1000
        if len(content) > max_length:
            content = content[:max_length]

        return {"title": title, "content": content}
    except Exception as e:
        return {"error": str(e)}


async def scheduled_parsing(bot, url: str, state: FSMContext):
    from admin_handlers import send_auto_parsing_to_admin
    global processed_links

    try:
        # Запрос к странице
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Поиск активной вкладки
        active_tab = soup.find("div", class_="tab-pane active fade show")
        if active_tab:
            print("Найдена активная вкладка с новостями.")
            news_list = active_tab.find("div", class_="small-list-post col-lg-12")
            if news_list:
                print("Найден блок с новостями.")
                # Найдем все блоки с новостями
                news_blocks = news_list.find_all("div", class_="small-post clearfix")
                if news_blocks:
                    for news_block in news_blocks:
                        title_tag = news_block.find("a")
                        if title_tag:
                            title = title_tag.text.strip()
                            link = title_tag.get("href")
                            print(f"Найдено название новости: {title}, ссылка: {link}")

                            # Проверяем, была ли ссылка уже обработана
                            if link not in processed_links:
                                # Переход по ссылке и парсинг содержимого
                                news = parse_news(link)

                                if "error" not in news:
                                    # Отправляем новость в канал
                        

                                    # Отправляем результаты парсинга админу
                                    await send_auto_parsing_to_admin(bot, news, link,state)

                                    # Добавляем ссылку в обработанные и сохраняем
                                    processed_links.add(link)
                                    save_processed_links()
                                else:
                                    print(f"Ошибка парсинга новости: {news['error']}")
                            else:
                                print("Ссылка уже обработана:", link)
                else:
                    print("Не удалось найти блоки с новостями.")
            else:
                print("Не удалось найти блок с новостями.")
        else:
            print("Не удалось найти активную вкладку с новостями.")

    except Exception as e:
        print(f"Ошибка парсинга страницы: {e}")

async def post_to_channel(bot: Bot, title: str, content: str, link: str):
    """
    Отправка спарсенной новости в Telegram канал.
    """
    try:
        message = f"<b>{title}</b>\n\n{content}\n\n<a href='{link}'>Читать далее</a>"
        await bot.send_message(chat_id=CHANNEL_ID, text=message, disable_web_page_preview=False)
    except Exception as e:
        print(f"Ошибка отправки в канал: {e}")