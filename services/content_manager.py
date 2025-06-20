import asyncio
import logging
from typing import List, Dict
from aiogram import Bot
from database.models import DatabaseModels
from services.news_parser import NewsParser
from services.ai_processor import AIProcessor

logger = logging.getLogger(__name__)


class ContentManager:
    def __init__(self, bot: Bot, db: DatabaseModels):
        self.bot = bot
        self.db = db
        self.ai_processor = AIProcessor()

    async def process_and_publish_news(self):
        """Обработка и публикация новостей с ИИ"""
        try:
            logger.info("Начинаем обработку новостей с ИИ...")

            # Получаем активные каналы
            channels = await self.db.get_channels()
            active_channels = [ch for ch in channels if ch['is_active']]

            if not active_channels:
                logger.info("Нет активных каналов для публикации")
                return

            # Получаем источники новостей
            sources = await self.db.get_news_sources()
            if not sources:
                logger.info("Нет активных источников новостей")
                return

            # Парсим новости
            async with NewsParser() as parser:
                all_news = await parser.get_news_from_sources(sources)

            if not all_news:
                logger.info("Не удалось получить новости")
                return

            logger.info(f"Получено {len(all_news)} новостей для ИИ обработки")

            # Обрабатываем новости через ИИ
            style = await self.db.get_setting("default_style") or "engaging"
            processed_posts = await self.ai_processor.process_news_batch(
                all_news, style, max_posts=3
            )

            if not processed_posts:
                logger.warning("ИИ не смог обработать ни одной новости")
                return

            logger.info(f"ИИ обработал {len(processed_posts)} постов")

            # Публикуем в каналы
            published_count = 0
            for channel in active_channels:
                for post in processed_posts[:channel['posts_per_day']]:
                    success = await self._publish_post_to_channel(
                        channel['channel_id'],
                        post['content']
                    )
                    if success:
                        published_count += 1
                        # Сохраняем в БД
                        await self._save_published_post(post, channel['channel_id'])

                    # Пауза между публикациями
                    await asyncio.sleep(2)

            logger.info(f"Опубликовано {published_count} постов в {len(active_channels)} каналов")

        except Exception as e:
            logger.error(f"Ошибка в процессе обработки новостей: {str(e)}")

    async def _publish_post_to_channel(self, channel_id: str, content: str) -> bool:
        """Публикация поста в канал"""
        try:
            await self.bot.send_message(
                chat_id=channel_id,
                text=content,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

            logger.info(f"Пост опубликован в канал {channel_id}")
            return True

        except Exception as e:
            logger.error(f"Ошибка публикации в канал {channel_id}: {str(e)}")
            return False

    async def _save_published_post(self, post: Dict, channel_id: str):
        """Сохранение опубликованного поста в БД"""
        try:
            # Здесь можно сохранить информацию о посте
            # Пока что просто логируем
            logger.info(f"Сохранен пост в БД для канала {channel_id}")
        except Exception as e:
            logger.error(f"Ошибка сохранения поста: {str(e)}")

    async def test_ai_processing(self) -> Dict:
        """Тестирование ИИ обработки"""
        try:
            # Тестируем подключение к OpenAI
            test_result = await self.ai_processor.test_ai_connection()

            if not test_result['success']:
                return {
                    'success': False,
                    'error': f"Ошибка подключения к OpenAI: {test_result['error']}"
                }

            # Получаем тестовую новость
            sources = await self.db.get_news_sources()
            async with NewsParser() as parser:
                news = await parser.get_news_from_sources(sources)

            if not news:
                return {
                    'success': False,
                    'error': "Нет новостей для тестирования"
                }

            # Обрабатываем одну новость
            test_post = await self.ai_processor.create_post(news[0])

            if test_post:
                return {
                    'success': True,
                    'original_title': test_post['original_title'],
                    'processed_content': test_post['content'][:200] + "...",
                    'style': test_post['style'],
                    'hashtags': test_post['hashtags']
                }
            else:
                return {
                    'success': False,
                    'error': "ИИ не смог обработать тестовую новость"
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def get_latest_news(self, limit: int = 10) -> List[Dict]:
        """Получение последних новостей"""
        try:
            sources = await self.db.get_news_sources()

            async with NewsParser() as parser:
                news = await parser.get_news_from_sources(sources)

            return news[:limit]

        except Exception as e:
            logger.error(f"Ошибка получения новостей: {str(e)}")
            return []