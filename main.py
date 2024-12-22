import os
import threading
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import telebot
import re
import datetime

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')  # Хост для Flask
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))  # Порт для Flask

if not API_KEY or not SECRET_KEY or not TELEGRAM_TOKEN:
    raise ValueError("Необходимы API_KEY, SECRET_KEY и TELEGRAM_TOKEN в файле .env")

# Flask-приложение
app = Flask(__name__)
app.secret_key = SECRET_KEY

API_ENDPOINT = "https://api.elsevier.com/content/search/scopus"

def format_title(title):
    """Удаляем HTML-теги и форматируем название статьи"""
    clean_title = re.sub(r"<[^>]+>", "", title)  # Убираем все HTML-теги
    return clean_title

@app.route('/Scopus', methods=['GET'])
def scopus_search():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Пожалуйста, укажите параметр 'query'"}), 400

    # Выполнение поиска в Scopus API
    try:
        params = {
            'query': f'TITLE-ABS-KEY("{query}")',
            'count': 5,  # Ограничение на 5 результатов
            'start': 0,
            'sort': 'relevancy',
            'apiKey': API_KEY,
            'field': 'dc:title,prism:doi,prism:publicationName,prism:coverDate,prism:url,dc:creator'
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

        return jsonify({"query": query, "results": articles})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/Quote', methods=['GET'])
def get_quota():
    """Получение информации о квотах API"""
    try:
        headers = {
            'Accept': 'application/json',
            'X-ELS-APIKey': API_KEY
        }
        response = requests.get(API_ENDPOINT, headers=headers, params={"query": "test", "count": 1})
        quota_info = {
            "X-RateLimit-Limit": response.headers.get('X-RateLimit-Limit', 'Неизвестно'),
            "X-RateLimit-Remaining": response.headers.get('X-RateLimit-Remaining', 'Неизвестно'),
            "X-RateLimit-Reset": response.headers.get('X-RateLimit-Reset', 'Неизвестно')
        }
        return jsonify(quota_info)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# Telegram-бот
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['scopus', 'Scopus'])
@bot.message_handler(func=lambda message: message.text.lower().startswith('/scopus'))
def handle_scopus(message):
    query = re.sub(r"^/scopus", "", message.text, flags=re.IGNORECASE).strip()
    if not query:
        bot.reply_to(message, "Пожалуйста, укажите поисковый запрос. Например: /scopus methane pyrolysis")
        return

    bot.reply_to(message, f"Ищу статьи по запросу: {query}...")

    # Отправляем запрос к Flask-приложению
    try:
        response = requests.get(f"http://{FLASK_HOST}:{FLASK_PORT}/Scopus", params={"query": query})
        response.raise_for_status()

        data = response.json()
        if "error" in data:
            bot.send_message(message.chat.id, f"Ошибка: {data['error']}")
            return

        articles = data.get("results", [])
        if not articles:
            bot.send_message(message.chat.id, "Ничего не найдено по вашему запросу.")
            return

        # Формируем сообщение с результатами
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

    # Отправляем запрос к Flask-приложению
    try:
        response = requests.get(f"http://{FLASK_HOST}:{FLASK_PORT}/Quote")
        response.raise_for_status()

        quota_info = response.json()
        reset_time = quota_info.get('X-RateLimit-Reset', 'Неизвестно')
        if reset_time.isdigit():
            reset_time = datetime.datetime.fromtimestamp(int(reset_time)).strftime('%Y-%m-%d %H:%M:%S')
        response_message = (
            f"Информация о квотах API:\n"
            f"Лимит запросов в сутки: {quota_info.get('X-RateLimit-Limit', 'Неизвестно')}\n"
            f"Оставшиеся запросы: {quota_info.get('X-RateLimit-Remaining', 'Неизвестно')}\n"
            f"Сброс квот: {reset_time}\n"
        )
        bot.send_message(message.chat.id, response_message)

    except requests.exceptions.RequestException as e:
        bot.send_message(message.chat.id, f"Ошибка при получении информации о квотах: {e}")

# Функция для запуска Flask
def run_flask():
    app.run(host=FLASK_HOST, port=FLASK_PORT)

# Функция для запуска Telegram-бота
def run_bot():
    bot.polling()

# Основной запуск
if __name__ == '__main__':
    # Создаем два потока: один для Flask, другой для Telegram-бота
    flask_thread = threading.Thread(target=run_flask)
    bot_thread = threading.Thread(target=run_bot)

    flask_thread.start()
    bot_thread.start()

    flask_thread.join()
    bot_thread.join()
