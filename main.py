# main.py - УПРОЩЕННАЯ ВЕРСИЯ без внешних зависимостей
import asyncio
import logging
import os
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

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


class ContentBot:
    def __init__(self):
        if not config.validate_config():
            print("❌ Ошибка конфигурации!")
            sys.exit(1)

        self.bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        self.db = None
        self.content_manager = None
        self.scheduler = None
        self.monitor = None
        self.smart_analyzer = None

        print(f"✅ Бот инициализирован с токеном: {config.BOT_TOKEN[:10]}...")

    async def setup_database(self):
        """Настройка базы данных"""
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

        try:
            for name, url, source_type, category in default_sources:
                await self.db.add_news_source(name, url, source_type, category)
        except:
            pass  # Источники уже добавлены

        logger.info("✅ База данных готова")

    async def setup_services(self):
        """Настройка сервисов"""
        self.content_manager = ContentManager(self.bot, self.db)
        self.scheduler = PostScheduler(self.content_manager, self.db)
        self.monitor = SmartMonitor(self.db, self.scheduler)

        # Пытаемся инициализировать ИИ-анализатор
        try:
            from services.smart_analyzer import SmartContentAnalyzer
            self.smart_analyzer = SmartContentAnalyzer(self.db)
            logger.info("✅ ИИ-анализатор инициализирован")
        except Exception as e:
            logger.warning(f"⚠️ ИИ-анализатор не доступен: {e}")
            self.smart_analyzer = None

        # Восстанавливаем задачи из БД
        await self.scheduler.restore_jobs_from_db()

        logger.info("✅ Сервисы готовы")

    def setup_handlers(self):
        """Настройка обработчиков"""
        try:
            from handlers import admin
            self.dp.include_router(admin.router)

            # Пытаемся подключить аналитику
            try:
                from handlers import analytics
                self.dp.include_router(analytics.router)
                logger.info("✅ Аналитика подключена")
            except Exception as e:
                logger.warning(f"⚠️ Аналитика не подключена: {e}")

            # Добавляем middleware для передачи зависимостей
            @self.dp.message.middleware()
            async def db_middleware(handler, event, data):
                data['db'] = self.db
                data['content_manager'] = self.content_manager
                data['scheduler'] = self.scheduler
                data['monitor'] = self.monitor
                data['smart_analyzer'] = self.smart_analyzer

                return await handler(event, data)

            logger.info("✅ Обработчики настроены")
            print("✅ Обработчики подключены")

        except Exception as e:
            logger.error(f"❌ Ошибка подключения обработчиков: {str(e)}")
            print(f"❌ Ошибка обработчиков: {str(e)}")

    async def start_polling(self):
        """Запуск бота в режиме polling"""
        try:
            await self.setup_database()
            await self.setup_services()
            self.setup_handlers()

            # Запускаем планировщик
            self.scheduler.start()

            # Запускаем мониторинг
            asyncio.create_task(self.monitor.start_monitoring())

            ai_status = "с ИИ-поддержкой" if self.smart_analyzer else "без ИИ"

            logger.info(f"🚀 Бот запущен {ai_status}")
            print("🚀 Бот запущен успешно!")
            print("📝 Логи сохраняются в bot.log")
            print("📅 Планировщик работает")
            print("🔍 Система мониторинга активна")

            if self.smart_analyzer:
                print("🧠 ИИ-анализатор готов к работе")
            else:
                print("⚠️ ИИ-анализатор недоступен")

            print("⏹ Для остановки нажмите Ctrl+C")

            await self.bot.delete_webhook(drop_pending_updates=True)
            await self.dp.start_polling(self.bot)

        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {str(e)}")
            print(f"❌ Ошибка: {str(e)}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Корректное завершение работы"""
        try:
            if self.scheduler:
                self.scheduler.stop()
                logger.info("✅ Планировщик остановлен")

            if self.monitor:
                await self.monitor.stop_monitoring()
                logger.info("✅ Мониторинг остановлен")

            await self.bot.session.close()
            logger.info("✅ Бот корректно завершил работу")
        except Exception as e:
            logger.error(f"❌ Ошибка при завершении работы: {str(e)}")


async def main():
    """Основная функция запуска"""
    bot = ContentBot()

    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("📴 Получен сигнал завершения")
        print("\n⏹ Бот остановлен")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {str(e)}")
        print(f"❌ Критическая ошибка: {str(e)}")


if __name__ == "__main__":
    print("🚀 Запуск Content Manager Bot v3.0...")

    if not config.validate_config():
        print("❌ Ошибка в конфигурации!")
        exit(1)

    asyncio.run(main())