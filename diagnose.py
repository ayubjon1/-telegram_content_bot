#!/usr/bin/env python3
"""
Скрипт диагностики Content Manager Bot
Проверяет все компоненты и исправляет проблемы
"""

import os
import sys
import importlib
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple
import aiosqlite


class BotDiagnostic:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixed = []

    def check_python_version(self):
        """Проверка версии Python"""
        print("🔍 Проверяю версию Python...")
        if sys.version_info < (3, 8):
            self.errors.append(f"❌ Требуется Python 3.8+, у вас {sys.version}")
            return False
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True

    def check_dependencies(self):
        """Проверка зависимостей"""
        print("\n🔍 Проверяю зависимости...")

        required_packages = {
            'aiogram': '3.3.0',
            'openai': '1.3.8',
            'numpy': None,
            'sklearn': None,
            'aiohttp': '3.9.1',
            'aiosqlite': '0.19.0',
            'psutil': None,
            'dotenv': None
        }

        missing = []

        for package, version in required_packages.items():
            try:
                if package == 'sklearn':
                    importlib.import_module('sklearn')
                elif package == 'dotenv':
                    importlib.import_module('dotenv')
                else:
                    importlib.import_module(package)
                print(f"✅ {package} установлен")
            except ImportError:
                missing.append(package)
                self.errors.append(f"❌ Пакет {package} не установлен")

        if missing:
            print(f"\n⚠️ Отсутствуют пакеты: {', '.join(missing)}")
            print("Установите их командой: pip install -r requirements.txt")
            return False

        return True

    def check_project_structure(self):
        """Проверка структуры проекта"""
        print("\n🔍 Проверяю структуру проекта...")

        required_dirs = ['handlers', 'services', 'utils', 'database', 'data', 'logs']
        required_files = {
            'main.py': 'Основной файл запуска',
            'config.py': 'Конфигурация',
            'requirements.txt': 'Зависимости',
            'handlers/__init__.py': 'Инициализация handlers',
            'services/__init__.py': 'Инициализация services',
            'utils/__init__.py': 'Инициализация utils',
            'database/__init__.py': 'Инициализация database',
            'database/models.py': 'Модели БД',
            'utils/keyboards.py': 'Клавиатуры',
        }

        # Проверяем директории
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                print(f"📁 Создаю директорию {dir_name}/")
                Path(dir_name).mkdir(exist_ok=True)
                self.fixed.append(f"Создана директория {dir_name}")
            else:
                print(f"✅ Директория {dir_name}/ существует")

        # Проверяем файлы
        for file_path, description in required_files.items():
            if not Path(file_path).exists():
                self.warnings.append(f"⚠️ Отсутствует файл {file_path} ({description})")

                # Создаем пустые __init__.py
                if file_path.endswith('__init__.py'):
                    Path(file_path).touch()
                    self.fixed.append(f"Создан файл {file_path}")
            else:
                print(f"✅ Файл {file_path} существует")

        return True

    def check_configuration(self):
        """Проверка конфигурации"""
        print("\n🔍 Проверяю конфигурацию...")

        config_files = ['.env', 'config.json', 'keys.py']
        config_found = False

        for config_file in config_files:
            if Path(config_file).exists():
                print(f"✅ Найден файл конфигурации: {config_file}")
                config_found = True
                break

        if not config_found:
            self.errors.append("❌ Не найден файл конфигурации (.env, config.json или keys.py)")
            print("\n💡 Запустите quick_setup.py для создания конфигурации")
            return False

        # Проверяем импорт конфигурации
        try:
            from config import config
            if config.validate_config():
                print("✅ Конфигурация валидна")
                return True
            else:
                self.errors.append("❌ Конфигурация не прошла валидацию")
                return False
        except Exception as e:
            self.errors.append(f"❌ Ошибка импорта конфигурации: {str(e)}")
            return False

    def check_ai_components(self):
        """Проверка ИИ компонентов"""
        print("\n🔍 Проверяю ИИ компоненты...")

        ai_files = {
            'services/smart_analyzer.py': 'Умный анализатор',
            'services/performance_tracker.py': 'Трекер производительности',
            'handlers/ai_control.py': 'ИИ панель управления',
            'handlers/ai_management.py': 'Управление ИИ',
            'handlers/analytics_pro.py': 'Профессиональная аналитика'
        }

        for file_path, description in ai_files.items():
            if Path(file_path).exists():
                print(f"✅ {description} найден")
            else:
                self.warnings.append(f"⚠️ Отсутствует {description} ({file_path})")

        return True

    def check_imports(self):
        """Проверка основных импортов"""
        print("\n🔍 Проверяю импорты...")

        test_imports = [
            ('aiogram', 'Telegram Bot Framework'),
            ('openai', 'OpenAI API'),
            ('numpy', 'NumPy'),
            ('sklearn', 'Scikit-learn'),
            ('psutil', 'System monitoring')
        ]

        all_ok = True

        for module_name, description in test_imports:
            try:
                if module_name == 'sklearn':
                    importlib.import_module('sklearn')
                else:
                    importlib.import_module(module_name)
                print(f"✅ {description} работает")
            except ImportError as e:
                self.errors.append(f"❌ Не удается импортировать {module_name}: {str(e)}")
                all_ok = False

        return all_ok

    async def check_database(self):
        """Проверка базы данных"""
        print("\n🔍 Проверяю базу данных...")

        try:
            from database.models import DatabaseModels
            from config import DATABASE_PATH

            db = DatabaseModels(DATABASE_PATH)
            await db.init_database()

            # Проверяем таблицы
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = await cursor.fetchall()
                table_names = [t[0] for t in tables]

                required_tables = ['channels', 'news_sources', 'settings', 'posts', 'performance_metrics']

                for table in required_tables:
                    if table in table_names:
                        print(f"✅ Таблица {table} существует")
                    else:
                        self.warnings.append(f"⚠️ Таблица {table} отсутствует")

            return True

        except Exception as e:
            self.errors.append(f"❌ Ошибка проверки БД: {str(e)}")
            return False

    def generate_report(self):
        """Генерация отчета диагностики"""
        print("\n" + "=" * 60)
        print("📊 ОТЧЕТ ДИАГНОСТИКИ")
        print("=" * 60)

        if not self.errors and not self.warnings:
            print("\n🎉 Все компоненты работают отлично!")
            print("✅ Бот готов к запуску")
        else:
            if self.errors:
                print(f"\n❌ Найдено ошибок: {len(self.errors)}")
                for error in self.errors:
                    print(f"   {error}")

            if self.warnings:
                print(f"\n⚠️ Найдено предупреждений: {len(self.warnings)}")
                for warning in self.warnings:
                    print(f"   {warning}")

        if self.fixed:
            print(f"\n🔧 Исправлено проблем: {len(self.fixed)}")
            for fix in self.fixed:
                print(f"   ✅ {fix}")

        print("\n📋 Рекомендации:")

        if self.errors:
            print("1. Исправьте критические ошибки")
            print("2. Запустите pip install -r requirements.txt")
            print("3. Проверьте конфигурацию (python quick_setup.py)")
        elif self.warnings:
            print("1. Бот может работать, но рекомендуется установить недостающие компоненты")
            print("2. Скопируйте ИИ компоненты из артефактов")
        else:
            print("1. Запустите бота: python main.py")
            print("2. Используйте /ai для доступа к ИИ функциям")

    def fix_common_issues(self):
        """Автоматическое исправление типичных проблем"""
        print("\n🔧 Пытаюсь исправить обнаруженные проблемы...")

        # Создаем отсутствующие __init__.py
        init_dirs = ['handlers', 'services', 'utils', 'database']
        for dir_name in init_dirs:
            init_path = Path(dir_name) / '__init__.py'
            if not init_path.exists() and Path(dir_name).exists():
                init_path.touch()
                self.fixed.append(f"Создан {init_path}")

        # Создаем .gitignore если отсутствует
        if not Path('.gitignore').exists():
            gitignore_content = """# Конфигурация
.env
config.json
keys.py
*.pyc
__pycache__/
data/*.db
logs/*.log
"""
            Path('.gitignore').write_text(gitignore_content)
            self.fixed.append("Создан .gitignore")

        return True


async def main():
    """Основная функция диагностики"""
    print("🤖 Content Manager Bot - Диагностика v1.0")
    print("=" * 60)

    diagnostic = BotDiagnostic()

    # Выполняем проверки
    diagnostic.check_python_version()
    diagnostic.check_project_structure()
    diagnostic.check_configuration()
    diagnostic.check_dependencies()
    diagnostic.check_ai_components()
    diagnostic.check_imports()

    # Асинхронные проверки
    await diagnostic.check_database()

    # Пытаемся исправить проблемы
    diagnostic.fix_common_issues()

    # Генерируем отчет
    diagnostic.generate_report()

    # Возвращаем код выхода
    if diagnostic.errors:
        return 1
    else:
        return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Диагностика прервана")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {str(e)}")
        sys.exit(1)