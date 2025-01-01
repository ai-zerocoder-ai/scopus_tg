import os
import requests
import telebot
import re
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
API_KEY = os.getenv('API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not API_KEY or not TELEGRAM_TOKEN:
    raise ValueError("Необходимы API_KEY и TELEGRAM_TOKEN в файле .env")

# Telegram-бот
bot = telebot.TeleBot(TELEGRAM_TOKEN)
API_ENDPOINT = "https://api.elsevier.com/content/search/scopus"

def format_title(title):
    """Удаляем HTML-теги из названия статьи"""
    return re.sub(r"<[^>]+>", "", title)

def search_scopus(query):
    """Ищем статьи в Scopus API"""
    params = {
        'query': f'TITLE-ABS-KEY("{query}")',
        'count': 5,  # Ограничение на 5 результатов
        'start': 0,
        'sort': 'relevancy',
        'apiKey': API_KEY,
        'field': 'dc:title,prism:doi,prism:publicationName,prism:coverDate,dc:creator'
    }

    headers = {'Accept': 'application/json'}
    response = requests.get(API_ENDPOINT, headers=headers, params=params)
    response.raise_for_status()
    response_data = response.json()

    results = response_data.get('search-results', {}).get('entry', [])
    articles = []
    for entry in results:
        articles.append({
            "title": format_title(entry.get('dc:title', 'Нет названия')),
            "doi": entry.get('prism:doi', ''),
            "publication_name": entry.get('prism:publicationName', 'Нет журнала'),
            "cover_date": entry.get('prism:coverDate', 'Нет даты'),
            "authors": entry.get('dc:creator', 'Неизвестен'),
            "url": f"https://doi.org/{entry.get('prism:doi', '')}" if entry.get('prism:doi') else 'Ссылка недоступна'
        })
    return articles

@bot.message_handler(commands=['scopus'])
def handle_scopus(message):
    query = re.sub(r"^/scopus", "", message.text, flags=re.IGNORECASE).strip()
    if not query:
        bot.reply_to(message, "Пожалуйста, укажите поисковый запрос. Например: /scopus methane pyrolysis")
        return

    bot.reply_to(message, f"Ищу статьи по запросу: {query}...")

    try:
        articles = search_scopus(query)
        if not articles:
            bot.send_message(message.chat.id, "Ничего не найдено по вашему запросу.")
            return

        response_message = f"Результаты поиска для \"{query}\":\n\n"
        for article in articles:
            response_message += (
                f"Название: {article['title']}\n"
                f"DOI: {article['doi']}\n"
                f"Журнал: {article['publication_name']}\n"
                f"Дата: {article['cover_date']}\n"
                f"Авторы: {article['authors']}\n"
                f"Ссылка: {article['url']}\n\n"
            )

        bot.send_message(message.chat.id, response_message)

    except requests.exceptions.RequestException as e:
        bot.send_message(message.chat.id, f"Ошибка при поиске: {e}")

@bot.message_handler(commands=['quote'])
def handle_quote(message):
    bot.reply_to(message, "Получаю информацию о квотах API...")

    try:
        headers = {
            'Accept': 'application/json',
            'X-ELS-APIKey': API_KEY
        }
        response = requests.get(API_ENDPOINT, headers=headers, params={"query": "test", "count": 1})
        response.raise_for_status()

        quota_info = {
            "X-RateLimit-Limit": response.headers.get('X-RateLimit-Limit', 'Неизвестно'),
            "X-RateLimit-Remaining": response.headers.get('X-RateLimit-Remaining', 'Неизвестно'),
            "X-RateLimit-Reset": response.headers.get('X-RateLimit-Reset', 'Неизвестно')
        }

        reset_time = quota_info.get('X-RateLimit-Reset', 'Неизвестно')
        if reset_time.isdigit():
            reset_time = datetime.datetime.fromtimestamp(int(reset_time)).strftime('%Y-%m-%d %H:%M:%S')

        response_message = (
            f"Статус квот на запросы по базе Scopus:\n"
            f"Лимит запросов: {quota_info.get('X-RateLimit-Limit', 'Неизвестно')}\n"
            f"Оставшиеся запросы: {quota_info.get('X-RateLimit-Remaining', 'Неизвестно')}\n"
            f"Сброс квот: {reset_time}\n"
        )
        bot.send_message(message.chat.id, response_message)

    except requests.exceptions.RequestException as e:
        bot.send_message(message.chat.id, f"Ошибка при получении информации о квотах: {e}")

if __name__ == '__main__':
    bot.polling()
