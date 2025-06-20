# main.py - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ ОШИБОК ИМПОРТА
import asyncio
import logging
import os
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

# Импорты наших модулей
from config import config, DATABASE_PATH
from database.models import DatabaseModels
from services.content_manager import ContentManager
from services.scheduler import PostScheduler
from utils.monitoring import SmartMonitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FixedContentBot:
    """Исправленная версия Content Manager Bot без ошибок импорта"""

    def __init__(self):
        if not config.validate_config():
            print("❌ Ошибка конфигурации!")
            sys.exit(1)

        self.bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()

        # Основные компоненты
        self.db = None
        self.content_manager = None
        self.scheduler = None
        self.monitor = None

        # ИИ компоненты (опциональные)
        self.smart_analyzer = None
        self.performance_tracker = None

        self.version = "3.0.1-fixed"
        self.startup_time = None

        print(f"🤖 Content Manager Bot v{self.version} - Исправленная версия")
        print(f"✅ Токен: {config.BOT_TOKEN[:10]}...")

    async def setup_database(self):
        """Настройка базы данных"""
        print("📊 Настройка базы данных...")

        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self.db = DatabaseModels(DATABASE_PATH)
        await self.db.init_database()

        # Добавляем источники новостей по умолчанию
        default_sources = [
            ("Lenta.ru", "https://lenta.ru/rss", "rss", "общее"),
            ("РИА Новости", "https://ria.ru/export/rss2/archive/index.xml", "rss", "общее"),
            ("ТАСС", "https://tass.ru/rss/v2.xml", "rss", "общее"),
            ("Российская газета", "https://rg.ru/xml/index.xml", "rss", "общее"),
        ]

        for name, url, source_type, category in default_sources:
            try:
                await self.db.add_news_source(name, url, source_type, category)
            except:
                pass  # Источники уже добавлены

        # Инициализируем базовые настройки
        default_settings = {
            'openai_model': 'gpt-4',
            'ai_temperature': '0.7',
            'ai_max_tokens': '800',
            'default_style': 'engaging',
            'max_posts_per_day': '20',
            'min_interval_minutes': '30'
        }

        for key, value in default_settings.items():
            try:
                existing = await self.db.get_setting(key)
                if not existing:
                    await self.db.set_setting(key, value)
            except:
                pass

        logger.info("✅ База данных настроена")

    async def setup_optional_ai_components(self):
        """Настройка ИИ компонентов (опциональные)"""
        print("🧠 Попытка инициализации ИИ-компонентов...")

        # Пытаемся загрузить дополнительные компоненты
        try:
            from services.smart_analyzer import SmartContentAnalyzer
            self.smart_analyzer = SmartContentAnalyzer(self.db)
            logger.info("✅ Умный анализатор подключен")
        except ImportError:
            logger.info("ℹ️ Умный анализатор не найден - это нормально")
            self.smart_analyzer = None
        except Exception as e:
            logger.warning(f"⚠️ Умный анализатор недоступен: {e}")
            self.smart_analyzer = None

        try:
            from services.performance_tracker import PerformanceTracker
            self.performance_tracker = PerformanceTracker(self.db)
            logger.info("✅ Трекер производительности подключен")
        except ImportError:
            logger.info("ℹ️ Трекер производительности не найден - это нормально")
            self.performance_tracker = None
        except Exception as e:
            logger.warning(f"⚠️ Трекер производительности недоступен: {e}")
            self.performance_tracker = None

    async def setup_core_services(self):
        """Настройка основных сервисов"""
        print("⚙️ Настройка основных сервисов...")

        # Content Manager
        self.content_manager = ContentManager(self.bot, self.db)

        # Планировщик
        self.scheduler = PostScheduler(self.content_manager, self.db)

        # Мониторинг
        self.monitor = SmartMonitor(self.db, self.scheduler)

        # Восстанавливаем состояние планировщика
        try:
            await self.scheduler.restore_jobs_from_db()
        except Exception as e:
            logger.warning(f"⚠️ Не удалось восстановить задачи планировщика: {e}")

        logger.info("✅ Основные сервисы готовы")

    def setup_handlers(self):
        """Настройка обработчиков с проверкой доступности"""
        print("🔧 Подключение обработчиков...")

        handlers_loaded = []
        handlers_failed = []

        # Основные обработчики (обязательные)
        try:
            from handlers import admin
            self.dp.include_router(admin.router)
            handlers_loaded.append("admin")
        except ImportError as e:
            logger.error(f"❌ Критическая ошибка: не найден handlers/admin.py: {e}")
            handlers_failed.append("admin")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки admin.py: {e}")
            handlers_failed.append("admin")

        # ИИ управление (новый модуль)
        try:
            from handlers import ai_management
            self.dp.include_router(ai_management.router)
            handlers_loaded.append("ai_management")
        except ImportError:
            logger.info("ℹ️ ai_management.py не найден - создайте этот файл")
            handlers_failed.append("ai_management")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки ai_management.py: {e}")
            handlers_failed.append("ai_management")

        # Дополнительные обработчики (опциональные)
        optional_handlers = [
            ("channels", "Управление каналами"),
            ("news", "Управление новостями"),
            ("settings", "Настройки"),
            ("ai_control", "ИИ панель"),
            ("analytics_pro", "Продвинутая аналитика")
        ]

        for handler_name, description in optional_handlers:
            try:
                handler_module = __import__(f"handlers.{handler_name}", fromlist=[handler_name])
                self.dp.include_router(handler_module.router)
                handlers_loaded.append(handler_name)
            except ImportError:
                logger.info(f"ℹ️ {handler_name}.py не найден - {description} недоступно")
                handlers_failed.append(handler_name)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки {handler_name}.py: {e}")
                handlers_failed.append(handler_name)

        # Middleware для передачи зависимостей
        @self.dp.message.middleware()
        async def dependencies_middleware(handler, event, data):
            data['db'] = self.db
            data['content_manager'] = self.content_manager
            data['scheduler'] = self.scheduler
            data['monitor'] = self.monitor
            data['smart_analyzer'] = self.smart_analyzer
            data['performance_tracker'] = self.performance_tracker
            return await handler(event, data)

        @self.dp.callback_query.middleware()
        async def callback_dependencies_middleware(handler, event, data):
            data['db'] = self.db
            data['content_manager'] = self.content_manager
            data['scheduler'] = self.scheduler
            data['monitor'] = self.monitor
            data['smart_analyzer'] = self.smart_analyzer
            data['performance_tracker'] = self.performance_tracker
            return await handler(event, data)

        # Отчет о загрузке
        print(f"✅ Загружены обработчики: {', '.join(handlers_loaded)}")
        if handlers_failed:
            print(f"⚠️ Не загружены: {', '.join(handlers_failed)}")

        logger.info(f"✅ Обработчики подключены: {len(handlers_loaded)}")

    async def setup_bot_commands(self):
        """Настройка команд бота"""
        commands = [
            BotCommand(command="start", description="🚀 Запуск бота"),
            BotCommand(command="help", description="❓ Справка"),
            BotCommand(command="status", description="📊 Статус системы"),
            BotCommand(command="ai", description="🤖 ИИ-панель (если доступно)"),
            BotCommand(command="health_check", description="🔍 Диагностика"),
        ]

        await self.bot.set_my_commands(commands)
        logger.info("✅ Команды бота настроены")

    async def start_background_services(self):
        """Запуск фоновых сервисов"""
        print("🔄 Запуск фоновых сервисов...")

        # Планировщик
        try:
            self.scheduler.start()
            logger.info("✅ Планировщик запущен")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска планировщика: {e}")

        # Мониторинг (неблокирующий)
        try:
            asyncio.create_task(self.monitor.start_monitoring())
            logger.info("✅ Мониторинг запущен")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска мониторинга: {e}")

        # Трекер производительности (если доступен)
        if self.performance_tracker:
            try:
                asyncio.create_task(self.performance_tracker.start_tracking())
                logger.info("✅ Трекер производительности запущен")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка запуска трекера: {e}")

    async def send_startup_notification(self):
        """Уведомление о запуске"""
        try:
            ai_features = []
            if self.smart_analyzer:
                ai_features.append("🧠 Smart Analyzer")
            if self.performance_tracker:
                ai_features.append("📊 Performance Tracker")

            ai_status = f"с {len(ai_features)} ИИ-компонентами" if ai_features else "базовая версия"

            startup_message = f"""
🚀 <b>Content Manager Bot v{self.version} запущен!</b>

✅ <b>Статус компонентов:</b>
• 📅 Планировщик: {'✅' if self.scheduler.running else '❌'}
• 🔍 Мониторинг: {'✅' if self.monitor.running else '❌'}
• 🤖 ИИ-компоненты: {len(ai_features)}

🛠️ <b>Версия:</b> {ai_status}

📊 <b>Система готова к работе!</b>
Используйте /start для начала работы.
            """

            await self.bot.send_message(
                chat_id=config.ADMIN_ID,
                text=startup_message,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

    async def start_polling(self):
        """Основной запуск бота"""
        try:
            self.startup_time = asyncio.get_event_loop().time()

            # Поэтапная инициализация
            await self.setup_database()
            await self.setup_optional_ai_components()
            await self.setup_core_services()
            await self.setup_bot_commands()
            self.setup_handlers()
            await self.start_background_services()

            # Определяем статус ИИ
            ai_components = []
            if self.smart_analyzer:
                ai_components.append("🧠 Smart Analyzer")
            if self.performance_tracker:
                ai_components.append("📊 Performance Tracker")

            ai_status = f"с {len(ai_components)} ИИ-компонентами" if ai_components else "базовая версия"

            print("\n" + "=" * 60)
            print(f"🤖 Content Manager Bot v{self.version}")
            print("=" * 60)
            print(f"✅ Успешно запущен {ai_status}")
            print("📝 Логи: bot.log")
            print("📅 Планировщик:", "активен" if self.scheduler.running else "неактивен")
            print("🔍 Мониторинг:", "активен" if self.monitor.running else "неактивен")

            if ai_components:
                print("🧠 ИИ-компоненты:")
                for component in ai_components:
                    print(f"   {component}")
            else:
                print("ℹ️ ИИ-компоненты не загружены (это нормально)")

            print("\n💡 Основные команды:")
            print("   /start - запуск и главное меню")
            print("   /status - статус системы")
            print("   /health_check - диагностика")
            if ai_components:
                print("   /ai - ИИ-панель управления")

            print(f"\n⏹ Для остановки: Ctrl+C")
            print("=" * 60)

            # Отправляем уведомление
            await self.send_startup_notification()

            logger.info(f"🚀 Бот v{self.version} успешно запущен")

            # Запускаем polling
            await self.bot.delete_webhook(drop_pending_updates=True)
            await self.dp.start_polling(self.bot)

        except Exception as e:
            logger.error(f"❌ Критическая ошибка запуска: {str(e)}")
            print(f"❌ Критическая ошибка: {str(e)}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Корректное завершение работы"""
        try:
            print("\n🔄 Завершение работы...")

            # Сохраняем состояние
            if self.scheduler:
                try:
                    await self.scheduler._save_jobs_to_db()
                    self.scheduler.stop()
                    logger.info("✅ Планировщик остановлен")
                except Exception as e:
                    logger.error(f"Ошибка остановки планировщика: {e}")

            # Останавливаем мониторинг
            if self.monitor:
                try:
                    await self.monitor.stop_monitoring()
                    logger.info("✅ Мониторинг остановлен")
                except Exception as e:
                    logger.error(f"Ошибка остановки мониторинга: {e}")

            # Останавливаем трекер
            if self.performance_tracker:
                try:
                    await self.performance_tracker.stop_tracking()
                    logger.info("✅ Трекер остановлен")
                except Exception as e:
                    logger.error(f"Ошибка остановки трекера: {e}")

            # Закрываем бота
            await self.bot.session.close()

            print("✅ Бот корректно завершил работу")
            logger.info("✅ Корректное завершение")

        except Exception as e:
            logger.error(f"❌ Ошибка при завершении: {str(e)}")


async def main():
    """Основная функция с улучшенной обработкой ошибок"""
    bot = FixedContentBot()

    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("📴 Завершение по запросу пользователя")
        print("\n⏹ Завершение работы")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {str(e)}")
        print(f"❌ Критическая ошибка: {str(e)}")


if __name__ == "__main__":
    print("🚀 Запуск Content Manager Bot v3.0.1 - Исправленная версия")
    print("🔧 Версия без ошибок импорта")

    # Проверяем конфигурацию
    if not config.validate_config():
        print("❌ Ошибка конфигурации!")
        print("   Создайте .env файл с BOT_TOKEN, OPENAI_API_KEY, ADMIN_ID")
        sys.exit(1)

    # Запускаем
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"💥 Фатальная ошибка: {str(e)}")
        sys.exit(1)