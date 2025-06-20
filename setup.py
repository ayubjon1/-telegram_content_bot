#!/usr/bin/env python3
"""
Скрипт первоначальной настройки Content Manager Bot
Запустите: python setup.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"   Текущая версия: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def install_dependencies():
    """Установка зависимостей"""
    print("\n📦 Установка зависимостей...")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены")
    except subprocess.CalledProcessError:
        print("❌ Ошибка установки зависимостей")
        print("   Попробуйте запустить: pip install -r requirements.txt")
        return False

    return True


def create_directories():
    """Создание необходимых директорий"""
    print("\n📁 Создание директорий...")

    directories = ['data', 'logs', 'utils']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ {directory}/")


def setup_configuration():
    """Настройка конфигурации"""
    print("\n⚙️ Настройка конфигурации")
    print("Выберите способ настройки:")
    print("1. Интерактивная настройка (рекомендуется)")
    print("2. Создать пример файлов")
    print("3. Пропустить")

    choice = input("\nВаш выбор (1-3): ").strip()

    if choice == "1":
        try:
            from utils.secure_config import ConfigSetup
            ConfigSetup.setup_config_interactive()
        except ImportError:
            print("❌ Модуль конфигурации не найден")
            create_example_files()
    elif choice == "2":
        create_example_files()
    else:
        print("⏭️ Настройка пропущена")


def create_example_files():
    """Создание примеров конфигурационных файлов"""
    print("\n📄 Создание примеров файлов...")

    # .env.example
    env_example = """# Content Manager Bot Configuration
# Скопируйте этот файл как .env и заполните реальными значениями
# НЕ ДОБАВЛЯТЬ В GIT!

# Основные токены (ОБЯЗАТЕЛЬНО)
BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
ADMIN_ID=123456789

# Дополнительные ключи (опционально)
NEWS_API_KEY=your_news_api_key_here

# RSS источники (разделены запятыми)
RSS_FEEDS=https://lenta.ru/rss,https://ria.ru/export/rss2/archive/index.xml,https://tass.ru/rss/v2.xml

# Настройки OpenAI
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=800
OPENAI_TEMPERATURE=0.7

# База данных
DATABASE_PATH=data/bot.db

# Пароль для зашифрованной конфигурации (если используется)
CONFIG_PASSWORD=your_secure_password_here
"""

    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_example)
    print("✅ .env.example")

    # config.json.example
    config_example = {
        "_comment": "Скопируйте как config.json и заполните реальными значениями",
        "BOT_TOKEN": "your_bot_token_here",
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "ADMIN_ID": 123456789,
        "NEWS_API_KEY": "your_news_api_key_here",
        "RSS_FEEDS": [
            "https://lenta.ru/rss",
            "https://ria.ru/export/rss2/archive/index.xml",
            "https://tass.ru/rss/v2.xml"
        ],
        "DATABASE_PATH": "data/bot.db",
        "OPENAI_MODEL": "gpt-4",
        "MAX_TOKENS": 800,
        "TEMPERATURE": 0.7
    }

    with open('config.json.example', 'w', encoding='utf-8') as f:
        json.dump(config_example, f, indent=2, ensure_ascii=False)
    print("✅ config.json.example")

    # .gitignore
    gitignore = """# Конфигурационные файлы (ВАЖНО!)
.env
config.json
config.encrypted
config.encrypted.salt
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

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
"""

    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore)
    print("✅ .gitignore")


def validate_setup():
    """Проверка корректности настройки"""
    print("\n🔍 Проверка настройки...")

    issues = []

    # Проверяем наличие конфигурации
    config_files = ['.env', 'config.json', 'config.encrypted']
    if not any(Path(f).exists() for f in config_files):
        issues.append("❌ Не найден файл конфигурации (.env, config.json или config.encrypted)")

    # Проверяем .gitignore
    if not Path('.gitignore').exists():
        issues.append("❌ Отсутствует .gitignore файл")

    # Проверяем директории
    required_dirs = ['data', 'handlers', 'services', 'utils']
    for directory in required_dirs:
        if not Path(directory).exists():
            issues.append(f"❌ Отсутствует директория {directory}/")

    if issues:
        print("⚠️ Найдены проблемы:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("✅ Настройка выглядит корректно")
        return True


def show_next_steps():
    """Показ следующих шагов"""
    print("\n" + "=" * 60)
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
    print("=" * 60)

    print("\n📋 Следующие шаги:")
    print("1. 🔑 Настройте конфигурацию:")

    if Path('.env').exists():
        print("   ✅ Файл .env уже создан")
    else:
        print("   📝 Скопируйте .env.example в .env")
        print("   ✏️  Заполните реальными токенами и ключами")

    print("\n2. 🤖 Получите необходимые токены:")
    print("   • Bot Token: https://t.me/BotFather")
    print("   • OpenAI API: https://platform.openai.com/")
    print("   • Ваш Telegram ID: https://t.me/userinfobot")

    print("\n3. 🚀 Запустите бота:")
    print("   python main.py")

    print("\n4. 📺 Настройте каналы:")
    print("   • Добавьте бота в канал как администратора")
    print("   • В боте: 📺 Мои каналы → ➕ Добавить канал")

    print("\n📚 Полная документация в README.md")
    print("🆘 При проблемах проверьте файл bot.log")


def main():
    """Основная функция настройки"""
    print("🤖 Content Manager Bot - Установка и настройка")
    print("=" * 60)

    # Проверки
    check_python_version()

    # Установка
    if not install_dependencies():
        return

    # Создание структуры
    create_directories()

    # Настройка конфигурации
    setup_configuration()

    # Проверка
    validate_setup()

    # Инструкции
    show_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Настройка прервана пользователем")
    except Exception as e:
        print(f"\n\n❌ Ошибка настройки: {str(e)}")
        print("   Попробуйте запустить настройку заново")