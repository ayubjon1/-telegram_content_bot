#!/usr/bin/env python3
"""
Инструмент диагностики Content Manager Bot
Запуск: python diagnostic.py
"""

import os
import sys
import importlib
from pathlib import Path
import logging


# Цвета для консоли
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_status(status, message):
    """Печать статуса с цветом"""
    if status == "OK":
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    elif status == "ERROR":
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    elif status == "WARNING":
        print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")
    elif status == "INFO":
        print(f"{Colors.BLUE}ℹ️ {message}{Colors.END}")


def check_python_version():
    """Проверка версии Python"""
    print(f"\n{Colors.BOLD}🐍 ПРОВЕРКА PYTHON{Colors.END}")

    version = sys.version_info
    if version >= (3, 8):
        print_status("OK", f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_status("ERROR", f"Python {version.major}.{version.minor}.{version.micro} - требуется 3.8+")
        return False


def check_file_structure():
    """Проверка структуры файлов"""
    print(f"\n{Colors.BOLD}📁 ПРОВЕРКА СТРУКТУРЫ ФАЙЛОВ{Colors.END}")

    required_files = [
        ("main.py", True),
        ("config.py", True),
        ("requirements.txt", True),
        (".env", False),
        ("handlers/__init__.py", True),
        ("handlers/admin.py", True),
        ("handlers/ai_management.py", False),
        ("services/__init__.py", True),
        ("services/content_manager.py", False),
        ("services/scheduler.py", False),
        ("utils/__init__.py", True),
        ("utils/keyboards.py", True),
        ("utils/monitoring.py", False),
        ("database/__init__.py", True),
        ("database/models.py", True),
    ]

    missing_critical = []
    missing_optional = []

    for file_path, is_critical in required_files:
        if Path(file_path).exists():
            print_status("OK", f"{file_path}")
        else:
            if is_critical:
                print_status("ERROR", f"{file_path} - ОТСУТСТВУЕТ (критический)")
                missing_critical.append(file_path)
            else:
                print_status("WARNING", f"{file_path} - отсутствует (опциональный)")
                missing_optional.append(file_path)

    return len(missing_critical) == 0, missing_critical, missing_optional


def check_dependencies():
    """Проверка зависимостей"""
    print(f"\n{Colors.BOLD}📦 ПРОВЕРКА ЗАВИСИМОСТЕЙ{Colors.END}")

    critical_deps = [
        "aiogram",
        "aiohttp",
        "aiosqlite",
        "python_dotenv"
    ]

    optional_deps = [
        "openai",
        "feedparser",
        "beautifulsoup4",
        "psutil",
        "numpy",
        "matplotlib"
    ]

    missing_critical = []
    missing_optional = []

    # Проверяем критические зависимости
    for dep in critical_deps:
        try:
            importlib.import_module(dep.replace("-", "_"))
            print_status("OK", f"{dep}")
        except ImportError:
            print_status("ERROR", f"{dep} - НЕ УСТАНОВЛЕН (критический)")
            missing_critical.append(dep)

    # Проверяем опциональные зависимости
    for dep in optional_deps:
        try:
            importlib.import_module(dep.replace("-", "_"))
            print_status("OK", f"{dep}")
        except ImportError:
            print_status("WARNING", f"{dep} - не установлен (опциональный)")
            missing_optional.append(dep)

    return len(missing_critical) == 0, missing_critical, missing_optional


def check_configuration():
    """Проверка конфигурации"""
    print(f"\n{Colors.BOLD}⚙️ ПРОВЕРКА КОНФИГУРАЦИИ{Colors.END}")

    issues = []

    # Проверяем .env файл
    if Path(".env").exists():
        print_status("OK", ".env файл найден")

        try:
            from dotenv import load_dotenv
            load_dotenv()

            # Проверяем основные переменные
            bot_token = os.getenv('BOT_TOKEN')
            openai_key = os.getenv('OPENAI_API_KEY')
            admin_id = os.getenv('ADMIN_ID')

            if bot_token:
                if len(bot_token) > 40 and ':' in bot_token:
                    print_status("OK", "BOT_TOKEN корректен")
                else:
                    print_status("ERROR", "BOT_TOKEN некорректен")
                    issues.append("BOT_TOKEN")
            else:
                print_status("ERROR", "BOT_TOKEN отсутствует")
                issues.append("BOT_TOKEN")

            if openai_key:
                if openai_key.startswith('sk-'):
                    print_status("OK", "OPENAI_API_KEY корректен")
                else:
                    print_status("WARNING", "OPENAI_API_KEY может быть некорректен")
            else:
                print_status("WARNING", "OPENAI_API_KEY отсутствует (ИИ будет недоступен)")

            if admin_id:
                try:
                    int(admin_id)
                    print_status("OK", "ADMIN_ID корректен")
                except ValueError:
                    print_status("ERROR", "ADMIN_ID должен быть числом")
                    issues.append("ADMIN_ID")
            else:
                print_status("ERROR", "ADMIN_ID отсутствует")
                issues.append("ADMIN_ID")

        except ImportError:
            print_status("ERROR", "python-dotenv не установлен")
            issues.append("python-dotenv")
    else:
        print_status("ERROR", ".env файл отсутствует")
        issues.append(".env file")

    return len(issues) == 0, issues


def check_imports():
    """Проверка импортов"""
    print(f"\n{Colors.BOLD}🔗 ПРОВЕРКА ИМПОРТОВ{Colors.END}")

    test_imports = [
        ("config", "config.py"),
        ("database.models", "database/models.py"),
        ("utils.keyboards", "utils/keyboards.py"),
        ("handlers.admin", "handlers/admin.py"),
    ]

    failed_imports = []

    for module_name, file_path in test_imports:
        try:
            importlib.import_module(module_name)
            print_status("OK", f"{module_name}")
        except Exception as e:
            print_status("ERROR", f"{module_name} - {str(e)}")
            failed_imports.append((module_name, str(e)))

    return len(failed_imports) == 0, failed_imports


def check_database():
    """Проверка базы данных"""
    print(f"\n{Colors.BOLD}🗄️ ПРОВЕРКА БАЗЫ ДАННЫХ{Colors.END}")

    try:
        # Создаем тестовую БД
        import aiosqlite
        import asyncio

        async def test_db():
            try:
                os.makedirs("data", exist_ok=True)
                async with aiosqlite.connect("data/test.db") as db:
                    await db.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
                    await db.commit()

                # Удаляем тестовую БД
                if os.path.exists("data/test.db"):
                    os.remove("data/test.db")

                return True
            except Exception as e:
                return False, str(e)

        result = asyncio.run(test_db())
        if result is True:
            print_status("OK", "SQLite работает корректно")
            return True
        else:
            print_status("ERROR", f"Ошибка SQLite: {result[1]}")
            return False

    except Exception as e:
        print_status("ERROR", f"aiosqlite недоступен: {str(e)}")
        return False


def suggest_fixes(missing_files, missing_deps, config_issues, import_errors):
    """Предложения по исправлению"""
    print(f"\n{Colors.BOLD}🔧 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ{Colors.END}")

    if missing_files:
        print(f"\n{Colors.YELLOW}📁 Отсутствующие критические файлы:{Colors.END}")
        for file in missing_files:
            print(f"   • {file}")
        print("   Решение: Скачайте недостающие файлы из проекта")

    if missing_deps:
        print(f"\n{Colors.YELLOW}📦 Отсутствующие критические зависимости:{Colors.END}")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("   Решение: pip install " + " ".join(missing_deps))

    if config_issues:
        print(f"\n{Colors.YELLOW}⚙️ Проблемы конфигурации:{Colors.END}")
        for issue in config_issues:
            print(f"   • {issue}")
        print("   Решение: Создайте/исправьте .env файл с корректными токенами")

    if import_errors:
        print(f"\n{Colors.YELLOW}🔗 Ошибки импорта:{Colors.END}")
        for module, error in import_errors:
            print(f"   • {module}: {error}")
        print("   Решение: Проверьте структуру файлов и зависимости")


def create_fix_script():
    """Создание скрипта автоисправления"""
    print(f"\n{Colors.BOLD}🛠️ СОЗДАНИЕ СКРИПТА ИСПРАВЛЕНИЯ{Colors.END}")

    fix_script = """#!/usr/bin/env python3
# auto_fix.py - Автоматическое исправление
import os
import subprocess
import sys

def install_dependencies():
    deps = ["aiogram==3.3.0", "aiohttp", "aiosqlite", "python-dotenv", "psutil"]
    for dep in deps:
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

def create_directories():
    dirs = ["data", "logs", "handlers", "services", "utils", "database"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def create_init_files():
    init_files = ["handlers/__init__.py", "services/__init__.py", "utils/__init__.py", "database/__init__.py"]
    for f in init_files:
        with open(f, "w") as file:
            file.write("# Auto-generated __init__.py\\n")

if __name__ == "__main__":
    print("🔧 Автоисправление...")
    try:
        install_dependencies()
        create_directories()
        create_init_files()
        print("✅ Исправление завершено!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
"""

    with open("auto_fix.py", "w", encoding="utf-8") as f:
        f.write(fix_script)

    print_status("OK", "Создан auto_fix.py")
    print("   Запустите: python auto_fix.py")


def main():
    """Основная функция диагностики"""
    print(f"{Colors.BOLD}🔍 ДИАГНОСТИКА CONTENT MANAGER BOT{Colors.END}")
    print("=" * 60)

    all_good = True

    # Проверки
    python_ok = check_python_version()
    files_ok, missing_files, _ = check_file_structure()
    deps_ok, missing_deps, _ = check_dependencies()
    config_ok, config_issues = check_configuration()
    imports_ok, import_errors = check_imports()
    db_ok = check_database()

    # Общий результат
    all_good = python_ok and files_ok and deps_ok and config_ok and imports_ok and db_ok

    print(f"\n{Colors.BOLD}📋 ИТОГОВЫЙ ОТЧЕТ{Colors.END}")
    print("=" * 60)

    if all_good:
        print_status("OK", "ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Бот готов к запуску.")
        print(f"\n{Colors.GREEN}🚀 Для запуска выполните: python main.py{Colors.END}")
    else:
        print_status("ERROR", "ОБНАРУЖЕНЫ ПРОБЛЕМЫ! Требуется исправление.")

        # Предложения по исправлению
        suggest_fixes(missing_files, missing_deps, config_issues, import_errors)

        # Создаем скрипт автоисправления
        create_fix_script()

        print(f"\n{Colors.BLUE}💡 БЫСТРОЕ ИСПРАВЛЕНИЕ:{Colors.END}")
        print("1. Запустите: python auto_fix.py")
        print("2. Создайте .env файл с токенами")
        print("3. Скачайте недостающие файлы")
        print("4. Запустите: python main.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹ Диагностика прервана{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}💥 Ошибка диагностики: {e}{Colors.END}")