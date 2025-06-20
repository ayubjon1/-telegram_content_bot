#!/usr/bin/env python3
"""
Быстрая настройка .env файла для Content Manager Bot
Запустите: python quick_setup.py
"""

import os
import re
from pathlib import Path


def create_gitignore():
    """Создание .gitignore файла"""
    gitignore_content = """# Конфигурационные файлы (ВАЖНО!)
.env
.env.local
.env.production
config.json
config.encrypted*
keys.py

# Логи и база данных
*.log
logs/
data/*.db
data/*.sqlite

# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
venv/
env/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
"""

    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("✅ Создан .gitignore файл")


def validate_bot_token(token):
    """Валидация токена бота"""
    pattern = r'^\d{8,10}:[a-zA-Z0-9_-]{35}$'
    return re.match(pattern, token) is not None


def validate_openai_key(key):
    """Валидация OpenAI ключа"""
    return key.startswith('sk-') and len(key) > 20


def validate_telegram_id(user_id):
    """Валидация Telegram ID"""
    try:
        uid = int(user_id)
        return 1 <= uid <= 999999999999
    except ValueError:
        return False


def main():
    print("🤖 Content Manager Bot - Быстрая настройка .env")
    print("=" * 60)

    # Проверяем существование .env
    if Path('.env').exists():
        overwrite = input("Файл .env уже существует. Перезаписать? (y/N): ").lower()
        if overwrite != 'y':
            print("❌ Настройка отменена")
            return

    print("\n📝 Пожалуйста, введите необходимые данные:")
    print("(Нажмите Enter для значений по умолчанию)")

    # Сбор обязательных данных
    while True:
        bot_token = input("\n🤖 Bot Token (от @BotFather): ").strip()
        if not bot_token:
            print("❌ Bot Token обязателен!")
            continue
        if not validate_bot_token(bot_token):
            print("❌ Неверный формат токена! Должен быть: 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
            continue
        break

    while True:
        openai_key = input("🧠 OpenAI API Key: ").strip()
        if not openai_key:
            print("❌ OpenAI API Key обязателен!")
            continue
        if not validate_openai_key(openai_key):
            print("❌ Неверный формат ключа! Должен начинаться с 'sk-'")
            continue
        break

    while True:
        admin_id = input("👤 Ваш Telegram ID: ").strip()
        if not admin_id:
            print("❌ Admin ID обязателен!")
            continue
        if not validate_telegram_id(admin_id):
            print("❌ Неверный Telegram ID! Должен быть числом от 1 до 999999999999")
            continue
        break

    # Дополнительные настройки
    print("\n⚙️ Дополнительные настройки (опционально):")

    news_api_key = input("📰 News API Key (Enter для пропуска): ").strip()

    print("\n📡 RSS источники:")
    print("По умолчанию: Lenta.ru, РИА, ТАСС, РГ")
    custom_rss = input("Свои RSS ленты через запятую (Enter для источников по умолчанию): ").strip()

    if custom_rss:
        rss_feeds = custom_rss
    else:
        rss_feeds = "https://lenta.ru/rss,https://ria.ru/export/rss2/archive/index.xml,https://tass.ru/rss/v2.xml,https://rg.ru/xml/index.xml"

    print("\n🤖 Настройки OpenAI:")
    openai_model = input("Модель (gpt-4): ").strip() or "gpt-4"
    max_tokens = input("Максимум токенов (800): ").strip() or "800"
    temperature = input("Температура 0.0-1.0 (0.7): ").strip() or "0.7"

    print("\n📊 Настройки публикации:")
    posts_per_day = input("Постов в день (5): ").strip() or "5"
    interval_hours = input("Интервал между постами в часах (3): ").strip() or "3"

    # Создание .env файла
    env_content = f"""# ========================================
# Content Manager Bot Configuration
# НЕ ДОБАВЛЯЙТЕ ЭТОТ ФАЙЛ В GIT!
# ========================================

# ОБЯЗАТЕЛЬНЫЕ НАСТРОЙКИ
BOT_TOKEN={bot_token}
OPENAI_API_KEY={openai_key}
ADMIN_ID={admin_id}

# ДОПОЛНИТЕЛЬНЫЕ API КЛЮЧИ
NEWS_API_KEY={news_api_key}

# RSS ИСТОЧНИКИ НОВОСТЕЙ
RSS_FEEDS={rss_feeds}

# НАСТРОЙКИ OPENAI
OPENAI_MODEL={openai_model}
OPENAI_MAX_TOKENS={max_tokens}
OPENAI_TEMPERATURE={temperature}

# ПУТИ И ФАЙЛЫ
DATABASE_PATH=data/bot.db

# НАСТРОЙКИ ПУБЛИКАЦИИ
POSTS_PER_DAY={posts_per_day}
POST_INTERVAL_HOURS={interval_hours}
REQUEST_TIMEOUT=30
MAX_NEWS_PER_SOURCE=10

# ЛОГИРОВАНИЕ
LOG_LEVEL=INFO
LOG_FILE=bot.log

# УВЕДОМЛЕНИЯ
NOTIFY_ERRORS=true
NOTIFY_SUCCESS=false
NOTIFY_DAILY_STATS=true

# БЕЗОПАСНОСТЬ
RATE_LIMIT_ENABLED=true
ENCRYPTION_ENABLED=false
"""

    # Сохраняем .env файл
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)

    # Создаем .gitignore
    create_gitignore()

    # Создаем директории
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    print("\n" + "=" * 60)
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
    print("=" * 60)

    print(f"\n✅ Создан .env файл с вашими настройками")
    print(f"✅ Создан .gitignore файл")
    print(f"✅ Созданы необходимые директории")

    print(f"\n📋 Что сделано:")
    print(f"  • Bot Token: {bot_token[:10]}...скрыт")
    print(f"  • OpenAI Key: {openai_key[:7]}...скрыт")
    print(f"  • Admin ID: {admin_id}")
    print(f"  • Модель OpenAI: {openai_model}")
    print(f"  • RSS источников: {len(rss_feeds.split(','))}")

    print(f"\n🚀 Следующие шаги:")
    print(f"  1. Установите зависимости: pip install -r requirements.txt")
    print(f"  2. Запустите бота: python main.py")
    print(f"  3. Добавьте бота в ваши каналы как администратора")
    print(f"  4. Настройте каналы через меню бота")

    print(f"\n⚠️ ВАЖНО:")
    print(f"  • Файл .env содержит секретные ключи")
    print(f"  • НЕ добавляйте .env в git репозиторий")
    print(f"  • .env уже добавлен в .gitignore")

    # Проверяем валидность конфигурации
    print(f"\n🔍 Проверка конфигурации...")
    try:
        from config import config
        if config.validate_config():
            print("✅ Конфигурация корректна!")
        else:
            print("❌ Ошибка в конфигурации")
    except Exception as e:
        print(f"⚠️ Не удалось проверить конфигурацию: {str(e)}")
        print("Попробуйте запустить: python main.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Настройка прервана пользователем")
    except Exception as e:
        print(f"\n\n❌ Ошибка: {str(e)}")
        print("Попробуйте создать .env файл вручную")