import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Основные настройки из .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')

# RSS ленты
RSS_FEEDS_STR = os.getenv('RSS_FEEDS', '')
RSS_FEEDS = [url.strip() for url in RSS_FEEDS_STR.split(',') if url.strip()] if RSS_FEEDS_STR else [
    "https://lenta.ru/rss",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://tass.ru/rss/v2.xml",
    "https://rg.ru/xml/index.xml"
]

# Пути и файлы
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot.db')

# Настройки приложения
POSTS_PER_DAY = int(os.getenv('POSTS_PER_DAY', 5))
POST_INTERVAL_HOURS = int(os.getenv('POST_INTERVAL_HOURS', 3))

# OpenAI настройки
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 800))
TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0.7))

# Промпт для обработки новостей
REWRITE_PROMPT = """
Переписать следующую новость, сохранив основную информацию, но изменив стиль изложения и структуру текста.
Требования:
1. Сохранить все важные факты и детали
2. Изменить стиль написания 
3. Использовать синонимы и перефразировать предложения
4. Добавить эмодзи для привлекательности
5. Текст должен быть уникальным и не нарушать авторские права
6. Максимум 500 символов

Новость для переписывания:
"""

# Настройки парсинга
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
MAX_NEWS_PER_SOURCE = int(os.getenv('MAX_NEWS_PER_SOURCE', 10))

# Категории новостей
NEWS_CATEGORIES = [
    "политика",
    "экономика",
    "технологии",
    "спорт",
    "культура",
    "наука",
    "общество"
]


# Проверка конфигурации
def validate_config():
    """Проверка обязательных настроек"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден в .env файле")
        return False

    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY не найден в .env файле")
        return False

    if not ADMIN_ID or ADMIN_ID == 0:
        print("❌ ADMIN_ID не найден в .env файле")
        return False

    return True


# Создаем объект config для совместимости
class Config:
    def __init__(self):
        self.BOT_TOKEN = BOT_TOKEN
        self.OPENAI_API_KEY = OPENAI_API_KEY
        self.ADMIN_ID = ADMIN_ID
        self.config_loaded = True

    def validate_config(self):
        return validate_config()


config = Config()