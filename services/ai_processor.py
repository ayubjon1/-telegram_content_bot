import openai
import asyncio
import logging
from typing import Optional, Dict, List
import re
import hashlib
from config import config

logger = logging.getLogger(__name__)


class AIProcessor:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = getattr(config, 'OPENAI_MODEL', 'gpt-4')
        self.max_tokens = getattr(config, 'MAX_TOKENS', 800)
        self.temperature = getattr(config, 'TEMPERATURE', 0.7)

    async def rewrite_news(self, title: str, content: str, style: str = "engaging") -> Optional[str]:
        """Переписывание новости с помощью ChatGPT"""
        try:
            # Объединяем заголовок и контент
            original_text = f"Заголовок: {title}\n\nТекст: {content}"

            # Ограничиваем длину входного текста
            if len(original_text) > 3000:
                original_text = original_text[:3000] + "..."

            # Выбираем промпт в зависимости от стиля
            prompt = self._get_style_prompt(style) + f"\n\nИсходная новость:\n{original_text}"

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный редактор и копирайтер. Твоя задача - переписывать новости, сохраняя все факты, но полностью меняя стиль изложения и структуру текста для избежания нарушения авторских прав."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            rewritten_text = response.choices[0].message.content.strip()

            # Проверяем качество переписанного текста
            if self._validate_rewritten_text(original_text, rewritten_text):
                logger.info(f"Успешно переписана новость: {title[:50]}...")
                return rewritten_text
            else:
                logger.warning(f"Переписанный текст не прошел валидацию: {title[:50]}...")
                return None

        except Exception as e:
            logger.error(f"Ошибка переписывания новости: {str(e)}")
            return None

    def _get_style_prompt(self, style: str) -> str:
        """Получение промпта в зависимости от стиля"""

        base_requirements = """
Требования к переписыванию:
1. Сохрани ВСЕ важные факты, цифры, имена, даты
2. Полностью измени структуру текста и порядок подачи информации
3. Используй синонимы и перефразируй предложения
4. Добавь подходящие эмодзи для привлекательности
5. Создай новый уникальный заголовок
6. Текст должен быть от 200 до 500 символов
7. В конце добавь 2-3 релевантных хештега
        """

        style_instructions = {
            "engaging": f"{base_requirements}\n\nСтиль: Привлекательный и интересный, с эмодзи и захватывающими формулировками. Используй яркие эпитеты и интригующие обороты.",

            "neutral": f"{base_requirements}\n\nСтиль: Нейтральный информационный стиль, сдержанный и объективный. Минимум эмодзи, факты без эмоциональной окраски.",

            "formal": f"{base_requirements}\n\nСтиль: Официальный деловой стиль, строгие формулировки, терминология. Используй конструкции 'сообщается', 'отмечается', 'по данным'.",

            "casual": f"{base_requirements}\n\nСтиль: Неформальный дружественный стиль, как будто рассказываешь другу. Простые слова, разговорные обороты."
        }

        return style_instructions.get(style, style_instructions["engaging"])

    def _validate_rewritten_text(self, original: str, rewritten: str) -> bool:
        """Валидация переписанного текста"""
        # Проверяем минимальную длину
        if len(rewritten) < 100:
            return False

        # Проверяем максимальную длину
        if len(rewritten) > 1000:
            return False

        # Проверяем, что текст действительно изменился
        similarity = self._calculate_similarity(original.lower(), rewritten.lower())
        if similarity > 0.7:  # Слишком похож на оригинал
            logger.warning(f"Текст слишком похож на оригинал (схожесть: {similarity:.2f})")
            return False

        # Проверяем наличие хештегов
        if not re.search(r'#\w+', rewritten):
            logger.warning("В переписанном тексте нет хештегов")
            return False

        return True

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Простой расчет похожести текстов по словам"""
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))

        if len(words1) == 0 or len(words2) == 0:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0

    async def generate_hashtags(self, content: str, category: str) -> List[str]:
        """Генерация хештегов для поста"""
        try:
            prompt = f"""
            Создай 2-3 релевантных хештега для новости из категории "{category}".

            Требования:
            1. Хештеги на русском языке
            2. Короткие и емкие (1-2 слова)
            3. Релевантные содержанию и категории
            4. Популярные в данной тематике

            Контент: {content[:200]}...

            Верни только хештеги через пробел, например: #новости #политика #россия
            """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по созданию хештегов для социальных сетей."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.5
            )

            hashtags_text = response.choices[0].message.content.strip()
            hashtags = re.findall(r'#\w+', hashtags_text)

            return hashtags[:3]  # Максимум 3 хештега

        except Exception as e:
            logger.error(f"Ошибка генерации хештегов: {str(e)}")
            # Возвращаем базовые хештеги по категории
            category_hashtags = {
                'политика': ['#политика', '#новости', '#россия'],
                'экономика': ['#экономика', '#финансы', '#бизнес'],
                'технологии': ['#технологии', '#инновации', '#наука'],
                'спорт': ['#спорт', '#соревнования', '#победа'],
                'наука': ['#наука', '#открытия', '#исследования'],
                'общество': ['#общество', '#люди', '#жизнь']
            }
            return category_hashtags.get(category, ['#новости', '#актуально'])

    async def create_post(self, news_item: Dict, style: str = "engaging") -> Optional[Dict]:
        """Создание готового поста из новости"""
        try:
            logger.info(f"Создаем пост из новости: {news_item['title'][:50]}...")

            # Переписываем новость
            rewritten_content = await self.rewrite_news(
                news_item['title'],
                news_item['content'],
                style
            )

            if not rewritten_content:
                logger.warning("Не удалось переписать новость")
                return None

            # Проверяем, есть ли уже хештеги в тексте
            existing_hashtags = re.findall(r'#\w+', rewritten_content)

            # Если хештегов мало, генерируем дополнительные
            if len(existing_hashtags) < 2:
                additional_hashtags = await self.generate_hashtags(
                    rewritten_content,
                    news_item.get('category', 'общее')
                )

                # Добавляем хештеги, которых еще нет
                for hashtag in additional_hashtags:
                    if hashtag not in existing_hashtags:
                        rewritten_content += f" {hashtag}"
                        existing_hashtags.append(hashtag)
                    if len(existing_hashtags) >= 3:
                        break

            return {
                'content': rewritten_content,
                'original_title': news_item['title'],
                'original_content': news_item['content'],
                'source_url': news_item.get('url', ''),
                'category': news_item.get('category', 'общее'),
                'source_id': news_item.get('source_id'),
                'hashtags': existing_hashtags,
                'style': style
            }

        except Exception as e:
            logger.error(f"Ошибка создания поста: {str(e)}")
            return None

    async def test_ai_connection(self) -> Dict:
        """Тестирование подключения к OpenAI"""
        try:
            test_prompt = "Привет! Это тест подключения к OpenAI API."

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": test_prompt}
                ],
                max_tokens=50
            )

            return {
                'success': True,
                'response': response.choices[0].message.content.strip(),
                'model': self.model,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'response': None,
                'model': self.model,
                'error': str(e)
            }

    async def process_news_batch(self, news_list: List[Dict], style: str = "engaging", max_posts: int = 5) -> List[
        Dict]:
        """Обработка пакета новостей"""
        processed_posts = []

        for i, news_item in enumerate(news_list[:max_posts]):
            try:
                logger.info(f"Обрабатываем новость {i + 1}/{min(len(news_list), max_posts)}")

                post = await self.create_post(news_item, style)
                if post:
                    processed_posts.append(post)

                # Небольшая пауза между запросами к API
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Ошибка обработки новости {i + 1}: {str(e)}")
                continue

        logger.info(f"Обработано {len(processed_posts)} постов из {len(news_list)} новостей")
        return processed_posts