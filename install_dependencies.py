#!/usr/bin/env python3
"""
Скрипт умной установки зависимостей для Content Manager Bot
Автоматически определяет версию Python и устанавливает совместимые пакеты
"""

import sys
import subprocess
import platform


def get_python_version():
    """Получение версии Python"""
    return sys.version_info


def install_package(package_spec):
    """Установка одного пакета"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_spec])
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    print("🤖 Content Manager Bot - Установка зависимостей")
    print("=" * 60)

    python_version = get_python_version()
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"🖥️ Платформа: {platform.system()} {platform.machine()}")

    # Базовые пакеты, которые работают везде
    base_packages = [
        "aiogram==3.3.0",
        "aiofiles==23.2.1",
        "openai==1.3.8",
        "aiohttp==3.9.1",
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "lxml==4.9.3",
        "aiosqlite==0.19.0",
        "feedparser==6.0.10",
        "python-dateutil==2.8.2",
        "pytz==2023.3",
        "psutil>=5.9.0",
        "cryptography>=41.0.0",
        "python-dotenv==1.0.0",
        "Pillow>=10.0.0",
        "nltk>=3.8.1",
        "textblob>=0.17.1"
    ]

    # Пакеты, зависящие от версии Python
    ml_packages = []

    if python_version >= (3, 13):
        print("\n⚠️ Python 3.13 обнаружен - используем последние версии пакетов")
        ml_packages = [
            "numpy",  # Последняя версия
            "scikit-learn",
            "pandas",
            "matplotlib"
        ]
        print("⚠️ TensorFlow пока не поддерживает Python 3.13")
    elif python_version >= (3, 9):
        ml_packages = [
            "numpy>=1.24.0,<2.0.0",
            "scikit-learn>=1.3.0",
            "pandas>=2.0.0",
            "matplotlib>=3.7.0",
            "tensorflow==2.15.0"
        ]
    else:
        ml_packages = [
            "numpy>=1.21.0,<1.24.0",
            "scikit-learn>=1.0.0",
            "pandas>=1.3.0",
            "matplotlib>=3.5.0",
            "tensorflow==2.13.0"
        ]

    all_packages = base_packages + ml_packages

    print(f"\n📦 Будет установлено {len(all_packages)} пакетов")

    # Обновляем pip
    print("\n🔄 Обновляю pip...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

    # Устанавливаем пакеты
    success = 0
    failed = []

    for i, package in enumerate(all_packages, 1):
        print(f"\n[{i}/{len(all_packages)}] Устанавливаю {package}...")
        if install_package(package):
            success += 1
            print(f"✅ {package} установлен")
        else:
            failed.append(package)
            print(f"❌ Ошибка установки {package}")

            # Пробуем альтернативные варианты для проблемных пакетов
            if "numpy" in package and python_version >= (3, 13):
                print("🔄 Пробую установить numpy без указания версии...")
                if install_package("numpy"):
                    success += 1
                    failed.remove(package)
                    print("✅ numpy установлен (последняя версия)")

    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ОТЧЕТ УСТАНОВКИ")
    print("=" * 60)
    print(f"✅ Успешно установлено: {success}/{len(all_packages)}")

    if failed:
        print(f"\n❌ Не удалось установить ({len(failed)}):")
        for package in failed:
            print(f"   • {package}")

        print("\n💡 Рекомендации:")
        print("1. Попробуйте установить проблемные пакеты вручную")
        print("2. Проверьте совместимость с вашей версией Python")
        print("3. Обновите setuptools: pip install --upgrade setuptools wheel")
    else:
        print("\n🎉 Все пакеты успешно установлены!")
        print("✅ Бот готов к запуску")

    # Проверяем критичные импорты
    print("\n🔍 Проверяю критичные импорты...")
    critical_imports = [
        ("aiogram", "Telegram Framework"),
        ("openai", "OpenAI API"),
        ("aiosqlite", "База данных")
    ]

    all_ok = True
    for module_name, description in critical_imports:
        try:
            __import__(module_name)
            print(f"✅ {description} работает")
        except ImportError:
            print(f"❌ {description} не работает")
            all_ok = False

    if all_ok:
        print("\n✅ Все критичные компоненты работают!")
        print("🚀 Запустите: python main.py")
    else:
        print("\n⚠️ Некоторые компоненты не работают")
        print("Бот может запуститься с ограниченным функционалом")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Установка прервана")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {str(e)}")
        sys.exit(1)