import aiohttp
import feedparser
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import re
from config import USER_AGENT, REQUEST_TIMEOUT, MAX_NEWS_PER_SOURCE

logger = logging.getLogger(__name__)


class NewsParser:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'User-Agent': USER_AGENT,
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def parse_rss_feed(self, url: str, source_name: str) -> List[Dict]:
        """Парсинг RSS ленты"""
        try:
            logger.info(f"Парсинг RSS: {source_name} ({url})")

            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} для {url}")
                    return []

                content = await response.text()
                feed = feedparser.parse(content)

                if not feed.entries:
                    logger.warning(f"Нет записей в RSS {source_name}")
                    return []

                news_items = []
                count = 0

                for entry in feed.entries:
                    if count >= MAX_NEWS_PER_SOURCE:
                        break

                    # Парсим дату публикации
                    pub_date = self._parse_date(entry)

                    # Проверяем актуальность (не старше 24 часов)
                    if pub_date and (datetime.now() - pub_date).days > 1:
                        continue

                    title = self._clean_text(entry.get('title', ''))
                    description = self._clean_text(entry.get('description', ''))
                    link = entry.get('link', '')

                    if not title or len(title) < 10:
                        continue

                    # Получаем полный текст статьи
                    full_content = await self._get_full_article(link)
                    content = full_content if full_content else description

                    if content and len(content) > 100:
                        news_item = {
                            'title': title,
                            'content': content,
                            'url': link,
                            'source': source_name,
                            'published_date': pub_date or datetime.now(),
                            'category': self._categorize_news(title + ' ' + content)
                        }

                        news_items.append(news_item)
                        count += 1

                logger.info(f"Получено {len(news_items)} новостей из {source_name}")
                return news_items

        except Exception as e:
            logger.error(f"Ошибка парсинга RSS {url}: {str(e)}")
            return []

    async def _get_full_article(self, url: str) -> Optional[str]:
        """Получение полного текста статьи"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Удаляем ненужные элементы
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                    element.decompose()

                # Ищем основной контент
                content_selectors = [
                    'article',
                    '.article-content', '.article-body', '.article-text',
                    '.content', '.post-content', '.entry-content',
                    '.text', '.story-text', '.news-text',
                    'main .text', 'main p'
                ]

                content = None
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = ' '.join([el.get_text(strip=True) for el in elements])
                        break

                if not content:
                    # Если не нашли по селекторам, берем все параграфы
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])

                if content:
                    content = self._clean_text(content)
                    # Ограничиваем длину
                    if len(content) > 2000:
                        content = content[:2000] + "..."

                    return content

        except Exception as e:
            logger.debug(f"Ошибка получения полного текста {url}: {str(e)}")

        return None

    def _clean_text(self, text: str) -> str:
        """Очистка текста"""
        if not text:
            return ""

        # Удаляем HTML теги
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()

        # Убираем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Убираем служебную информацию
        patterns_to_remove = [
            r'Читайте также:.*',
            r'Подписывайтесь.*',
            r'Следите за новостями.*',
            r'© \d{4}.*',
            r'Источник:.*'
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        return text.strip()

    def _parse_date(self, entry) -> Optional[datetime]:
        """Парсинг даты публикации"""
        date_fields = ['published', 'updated', 'pubDate']

        for field in date_fields:
            if hasattr(entry, field):
                date_str = getattr(entry, field, None)
                if date_str:
                    try:
                        # feedparser автоматически парсит даты
                        if hasattr(entry, f'{field}_parsed') and getattr(entry, f'{field}_parsed'):
                            import time
                            parsed_time = getattr(entry, f'{field}_parsed')
                            return datetime.fromtimestamp(time.mktime(parsed_time))
                    except:
                        pass

        return None

    def _categorize_news(self, text: str) -> str:
        """Категоризация новостей по ключевым словам"""
        text_lower = text.lower()

        categories = {
            'политика': [
                'политик', 'правительство', 'президент', 'министр', 'дума',
                'выборы', 'закон', 'власть', 'депутат', 'парламент'
            ],
            'экономика': [
                'экономика', 'рубль', 'доллар', 'банк', 'инфляция', 'бизнес',
                'компания', 'финансы', 'инвестиции', 'рынок', 'нефть', 'газ'
            ],
            'технологии': [
                'технология', 'интернет', 'компьютер', 'программа', 'ai',
                'искусственный интеллект', 'робот', 'инновации', 'стартап'
            ],
            'спорт': [
                'спорт', 'футбол', 'хоккей', 'олимпиада', 'чемпионат',
                'матч', 'игра', 'спортсмен', 'тренер', 'команда'
            ],
            'наука': [
                'наука', 'исследование', 'ученые', 'открытие', 'эксперимент',
                'медицина', 'космос', 'физика', 'химия', 'биология'
            ],
            'общество': [
                'общество', 'люди', 'социальный', 'образование', 'здоровье',
                'культура', 'искусство', 'кино', 'театр', 'музыка'
            ]
        }

        # Подсчитываем совпадения для каждой категории
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score

        # Возвращаем категорию с наибольшим количеством совпадений
        if category_scores:
            return max(category_scores, key=category_scores.get)

        return 'общее'

    async def get_news_from_sources(self, sources: List[Dict]) -> List[Dict]:
        """Получение новостей из всех источников"""
        all_news = []

        tasks = []
        for source in sources:
            if source['source_type'] == 'rss' and source['is_active']:
                task = self.parse_rss_feed(source['url'], source['name'])
                tasks.append((task, source['id']))

        if not tasks:
            logger.warning("Нет активных RSS источников")
            return []

        # Выполняем парсинг параллельно
        results = await asyncio.gather(*[task[0] for task in tasks], return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, list):  # Успешный результат
                source_id = tasks[i][1]
                for item in result:
                    item['source_id'] = source_id
                all_news.extend(result)
            else:  # Ошибка
                source_name = tasks[i][1]
                logger.error(f"Ошибка парсинга источника {source_name}: {result}")

        # Сортируем по дате публикации (новые сначала)
        all_news.sort(key=lambda x: x.get('published_date', datetime.min), reverse=True)

        # Убираем дубликаты по заголовкам
        unique_news = []
        seen_titles = set()

        for news in all_news:
            title_clean = re.sub(r'[^\w\s]', '', news['title'].lower())
            if title_clean not in seen_titles:
                seen_titles.add(title_clean)
                unique_news.append(news)

        logger.info(f"Получено {len(all_news)} новостей, уникальных: {len(unique_news)}")
        return unique_news

    async def test_source(self, url: str, source_name: str) -> Dict:
        """Тестирование одного источника"""
        try:
            news_items = await self.parse_rss_feed(url, source_name)
            return {
                'success': True,
                'news_count': len(news_items),
                'sample_titles': [item['title'] for item in news_items[:3]],
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'news_count': 0,
                'sample_titles': [],
                'error': str(e)
            }