# Telegram Scopus Bot

This project is a Flask-based API and Telegram bot that allows users to search for scientific articles in Scopus and retrieve information about API quotas. The bot supports commands like `/scopus` for article search and `/quote` for quota details.

## Features

- **Search for articles**: Use the `/scopus` command followed by a query to fetch the top 5 articles related to the search terms.
- **API quota information**: Use the `/quote` command to get information about your current Scopus API usage limits.
- **Formatted results**: The bot ensures that HTML tags (e.g., `<inf>`) in article titles are cleaned for better readability.
- **Case-insensitive commands**: The bot processes commands like `/scopus` or `/Scopus` without issues.

---

## Requirements

- Python 3.7+
- A valid Scopus API key
- A Telegram bot token

---

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root and add the following:
```plaintext
API_KEY=your_scopus_api_key
SECRET_KEY=your_flask_secret_key
TELEGRAM_TOKEN=your_telegram_bot_token
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

---

## Running the Application

### 1. Start the Bot and Flask API
```bash
python main.py
```

### 2. Test the Bot in Telegram
- Add the bot to a group or start a direct chat with it.
- Use the `/scopus` command followed by your query to search for articles.
- Use the `/quote` command to view API quota details.

---

## Commands

### `/scopus`
- Description: Search for articles on Scopus.
- Usage:
  ```
  /scopus methane pyrolysis
  ```
- The bot will return the top 5 articles matching the query.

### `/quote`
- Description: Get Scopus API quota information.
- Usage:
  ```
  /quote
  ```
- The bot will return information about daily limits, remaining requests, and quota reset time.

---

## Project Structure

```plaintext
├── main.py               # Main application file combining Flask API and Telegram bot
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not included in the repository)
├── README.md             # Project documentation
```

---

## Notes

- Ensure that the port specified in `.env` is open and accessible if deploying on a VPS.
- Use proper WSGI servers like Gunicorn for production deployment.

---

## License

This project is licensed under the MIT License.
