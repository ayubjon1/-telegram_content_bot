# services/smart_analyzer.py - Умный анализатор контента с ML
import re
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

logger = logging.getLogger(__name__)


class SmartContentAnalyzer:
    """Умный анализатор контента с предсказанием производительности"""

    def __init__(self, db=None):
        self.db = db
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.engagement_model = None
        self.content_history = []
        self.performance_data = {}

        # Веса для оценки качества
        self.quality_weights = {
            'readability': 0.2,
            'uniqueness': 0.15,
            'engagement_potential': 0.25,
            'emotional_score': 0.15,
            'structure_score': 0.15,
            'trend_relevance': 0.1
        }

        logger.info("🧠 Умный анализатор инициализирован")

    async def analyze_content(self, text: str, context: Optional[Dict] = None) -> Dict:
        """Комплексный анализ контента с ML предсказаниями"""
        try:
            # Базовые метрики
            basic_metrics = self._calculate_basic_metrics(text)

            # Качественные метрики
            quality_metrics = await self._calculate_quality_metrics(text)

            # Предсказание производительности
            performance_prediction = await self._predict_performance(text, context)

            # Рекомендации по улучшению
            recommendations = self._generate_recommendations(
                basic_metrics, quality_metrics, performance_prediction
            )

            # Общая оценка
            overall_score = self._calculate_overall_score(quality_metrics)

            # Оптимальное время публикации
            optimal_time = await self._predict_optimal_time(text, context)

            result = {
                'basic_metrics': basic_metrics,
                'quality_metrics': quality_metrics,
                'performance_prediction': performance_prediction,
                'recommendations': recommendations,
                'overall_score': overall_score,
                'optimal_publish_time': optimal_time,
                'analysis_timestamp': datetime.now().isoformat()
            }

            # Сохраняем результат для обучения
            await self._save_analysis_result(text, result)

            return result

        except Exception as e:
            logger.error(f"Ошибка анализа контента: {e}")
            return self._get_default_analysis()

    def _calculate_basic_metrics(self, text: str) -> Dict:
        """Расчет базовых метрик текста"""
        # Очищаем от HTML тегов
        clean_text = re.sub(r'<[^>]+>', '', text)

        # Считаем метрики
        words = clean_text.split()
        sentences = re.split(r'[.!?]+', clean_text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Эмодзи
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        emojis = emoji_pattern.findall(text)

        # Хештеги
        hashtags = re.findall(r'#\w+', text)

        # Вопросы
        questions = len(re.findall(r'\?', text))

        # Призывы к действию
        cta_patterns = [
            r'подпис', r'лайк', r'репост', r'коммент', r'поделись',
            r'нажми', r'перейди', r'узнай', r'получи', r'регистр'
        ]
        cta_count = sum(1 for pattern in cta_patterns if re.search(pattern, clean_text.lower()))

        return {
            'text_length': len(clean_text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': np.mean([len(w) for w in words]) if words else 0,
            'avg_sentence_length': np.mean([len(s.split()) for s in sentences]) if sentences else 0,
            'emoji_count': len(emojis),
            'hashtag_count': len(hashtags),
            'question_count': questions,
            'cta_count': cta_count,
            'unique_words': len(set(words)),
            'lexical_diversity': len(set(words)) / len(words) if words else 0
        }

    async def _calculate_quality_metrics(self, text: str) -> Dict:
        """Расчет качественных метрик"""
        # Читаемость (упрощенный Flesch Reading Ease для русского)
        basic_metrics = self._calculate_basic_metrics(text)

        # Адаптированная формула читаемости
        if basic_metrics['word_count'] > 0 and basic_metrics['sentence_count'] > 0:
            readability = 206.835 - 1.015 * (basic_metrics['word_count'] / basic_metrics['sentence_count']) - 84.6 * (
                        basic_metrics['avg_word_length'] / 10)
            readability = max(0, min(100, readability))  # Ограничиваем от 0 до 100
        else:
            readability = 50

        # Эмоциональная окраска
        emotional_score = await self._calculate_emotional_score(text)

        # Структурированность
        structure_score = self._calculate_structure_score(text)

        # Уникальность (сравнение с историей)
        uniqueness_score = await self._calculate_uniqueness(text)

        # Потенциал вовлечения
        engagement_potential = self._calculate_engagement_potential(basic_metrics, emotional_score)

        # Релевантность трендам
        trend_relevance = await self._calculate_trend_relevance(text)

        return {
            'readability': readability,
            'emotional_score': emotional_score,
            'structure_score': structure_score,
            'uniqueness': uniqueness_score,
            'engagement_potential': engagement_potential,
            'trend_relevance': trend_relevance
        }

    async def _calculate_emotional_score(self, text: str) -> float:
        """Оценка эмоциональной окраски текста"""
        # Эмоциональные маркеры
        positive_markers = [
            '!', '🔥', '💯', '✅', '👍', '😍', '🚀', '💪', '🎉', '❤️',
            'отлично', 'супер', 'круто', 'потрясающе', 'великолепно',
            'успех', 'победа', 'достижение', 'прорыв', 'революция'
        ]

        negative_markers = [
            '😢', '😡', '👎', '❌', '⚠️', '🚫',
            'плохо', 'ужасно', 'провал', 'проблема', 'кризис',
            'опасно', 'угроза', 'риск', 'потеря', 'крах'
        ]

        text_lower = text.lower()

        positive_count = sum(1 for marker in positive_markers if marker in text_lower)
        negative_count = sum(1 for marker in negative_markers if marker in text_lower)

        # Нормализуем от 0 до 1 (0.5 - нейтрально)
        total_markers = positive_count + negative_count
        if total_markers == 0:
            return 0.5

        emotional_score = (positive_count - negative_count) / total_markers
        return (emotional_score + 1) / 2  # Приводим к диапазону 0-1

    def _calculate_structure_score(self, text: str) -> float:
        """Оценка структурированности текста"""
        score = 0.0

        # Проверяем наличие структурных элементов
        if re.search(r'^\d+\.', text, re.MULTILINE):  # Нумерованные списки
            score += 0.2
        if re.search(r'^[•·\-\*]', text, re.MULTILINE):  # Маркированные списки
            score += 0.2
        if re.search(r'<b>.*?</b>', text):  # Выделение жирным
            score += 0.15
        if re.search(r'\n\n', text):  # Параграфы
            score += 0.15
        if len(re.findall(r'[А-ЯA-Z][^.!?]*[.!?]', text)) > 3:  # Несколько предложений
            score += 0.15
        if re.search(r'#\w+', text):  # Хештеги
            score += 0.15

        return min(1.0, score)

    async def _calculate_uniqueness(self, text: str) -> float:
        """Расчет уникальности относительно истории контента"""
        if not self.content_history:
            return 1.0

        # Векторизация текущего текста и истории
        try:
            all_texts = self.content_history[-100:] + [text]  # Последние 100 текстов

            if len(all_texts) < 2:
                return 1.0

            # TF-IDF векторизация
            vectors = self.vectorizer.fit_transform(all_texts)

            # Косинусное сходство с историческими текстами
            current_vector = vectors[-1]
            history_vectors = vectors[:-1]

            similarities = cosine_similarity(current_vector, history_vectors).flatten()

            # Максимальное сходство (чем меньше, тем уникальнее)
            max_similarity = np.max(similarities) if len(similarities) > 0 else 0

            uniqueness = 1.0 - max_similarity
            return max(0.0, min(1.0, uniqueness))

        except Exception as e:
            logger.error(f"Ошибка расчета уникальности: {e}")
            return 0.8

    def _calculate_engagement_potential(self, basic_metrics: Dict, emotional_score: float) -> float:
        """Расчет потенциала вовлечения"""
        score = 0.0

        # Оптимальная длина (150-300 символов)
        if 150 <= basic_metrics['text_length'] <= 300:
            score += 0.2
        elif 100 <= basic_metrics['text_length'] <= 400:
            score += 0.1

        # Эмодзи (2-5 оптимально)
        if 2 <= basic_metrics['emoji_count'] <= 5:
            score += 0.15
        elif 1 <= basic_metrics['emoji_count'] <= 7:
            score += 0.08

        # Вопросы вовлекают
        if basic_metrics['question_count'] > 0:
            score += 0.15

        # Призывы к действию
        if basic_metrics['cta_count'] > 0:
            score += 0.15

        # Хештеги (2-4 оптимально)
        if 2 <= basic_metrics['hashtag_count'] <= 4:
            score += 0.1

        # Эмоциональность
        if emotional_score > 0.6 or emotional_score < 0.4:  # Не нейтрально
            score += 0.15

        # Лексическое разнообразие
        if basic_metrics['lexical_diversity'] > 0.7:
            score += 0.1

        return min(1.0, score)

    async def _calculate_trend_relevance(self, text: str) -> float:
        """Оценка релевантности трендам"""
        # Трендовые слова (обновляются динамически)
        trend_keywords = [
            'ии', 'искусственный интеллект', 'нейросеть', 'chatgpt', 'ai',
            '2024', '2025', 'новый', 'революция', 'будущее', 'технологии',
            'криптовалюта', 'блокчейн', 'метавселенная', 'тренд'
        ]

        text_lower = text.lower()
        matches = sum(1 for keyword in trend_keywords if keyword in text_lower)

        # Нормализуем
        relevance = min(1.0, matches / 5)  # 5 трендовых слов = максимум
        return relevance

    async def _predict_performance(self, text: str, context: Optional[Dict] = None) -> Dict:
        """Предсказание производительности поста"""
        # Получаем метрики
        basic_metrics = self._calculate_basic_metrics(text)
        quality_metrics = await self._calculate_quality_metrics(text)

        # Базовые предсказания на основе исторических данных
        base_views = 100
        base_likes = 5
        base_shares = 1

        # Множители на основе качества
        quality_multiplier = quality_metrics['engagement_potential'] * 2 + 0.5

        # Корректировки
        if basic_metrics['emoji_count'] > 0:
            quality_multiplier *= 1.1
        if basic_metrics['question_count'] > 0:
            quality_multiplier *= 1.15
        if basic_metrics['hashtag_count'] > 0:
            quality_multiplier *= 1.05
        if quality_metrics['emotional_score'] > 0.7:
            quality_multiplier *= 1.2

        # Контекстные корректировки
        if context:
            if context.get('time_of_day') in ['morning', 'evening']:
                quality_multiplier *= 1.2
            if context.get('day_of_week') in ['saturday', 'sunday']:
                quality_multiplier *= 0.8

        # Финальные предсказания
        predicted_views = int(base_views * quality_multiplier)
        predicted_likes = int(base_likes * quality_multiplier * 1.2)
        predicted_shares = int(base_shares * quality_multiplier * 0.8)
        predicted_engagement_rate = (predicted_likes + predicted_shares) / predicted_views * 100

        return {
            'predicted_views': predicted_views,
            'predicted_likes': predicted_likes,
            'predicted_shares': predicted_shares,
            'predicted_engagement_rate': round(predicted_engagement_rate, 2),
            'confidence': 0.75,  # Уверенность в предсказании
            'factors': {
                'quality_multiplier': round(quality_multiplier, 2),
                'main_drivers': self._get_main_performance_drivers(basic_metrics, quality_metrics)
            }
        }

    def _get_main_performance_drivers(self, basic_metrics: Dict, quality_metrics: Dict) -> List[str]:
        """Определение основных факторов производительности"""
        drivers = []

        if quality_metrics['engagement_potential'] > 0.7:
            drivers.append("Высокий потенциал вовлечения")
        if quality_metrics['emotional_score'] > 0.7:
            drivers.append("Сильная эмоциональная окраска")
        if basic_metrics['question_count'] > 0:
            drivers.append("Интерактивный формат")
        if basic_metrics['emoji_count'] >= 2:
            drivers.append("Визуальная привлекательность")
        if quality_metrics['readability'] > 70:
            drivers.append("Отличная читаемость")
        if quality_metrics['trend_relevance'] > 0.5:
            drivers.append("Соответствие трендам")

        return drivers[:3]  # Топ-3 фактора

    def _generate_recommendations(self, basic_metrics: Dict, quality_metrics: Dict,
                                  performance_prediction: Dict) -> List[Dict]:
        """Генерация рекомендаций по улучшению"""
        recommendations = []

        # Анализ длины
        if basic_metrics['text_length'] < 100:
            recommendations.append({
                'type': 'length',
                'priority': 'high',
                'message': 'Увеличьте длину текста до 150-300 символов',
                'impact': '+20% к охвату'
            })
        elif basic_metrics['text_length'] > 500:
            recommendations.append({
                'type': 'length',
                'priority': 'medium',
                'message': 'Сократите текст для лучшей читаемости',
                'impact': '+15% к вовлечению'
            })

        # Эмодзи
        if basic_metrics['emoji_count'] == 0:
            recommendations.append({
                'type': 'emoji',
                'priority': 'high',
                'message': 'Добавьте 2-3 эмодзи для визуальной привлекательности',
                'impact': '+25% к лайкам'
            })
        elif basic_metrics['emoji_count'] > 7:
            recommendations.append({
                'type': 'emoji',
                'priority': 'low',
                'message': 'Уменьшите количество эмодзи',
                'impact': '+10% к доверию'
            })

        # Вопросы
        if basic_metrics['question_count'] == 0 and quality_metrics['engagement_potential'] < 0.5:
            recommendations.append({
                'type': 'question',
                'priority': 'medium',
                'message': 'Добавьте вопрос для повышения вовлечения',
                'impact': '+30% к комментариям'
            })

        # Хештеги
        if basic_metrics['hashtag_count'] == 0:
            recommendations.append({
                'type': 'hashtag',
                'priority': 'medium',
                'message': 'Добавьте 2-3 релевантных хештега',
                'impact': '+15% к обнаружению'
            })

        # Призыв к действию
        if basic_metrics['cta_count'] == 0:
            recommendations.append({
                'type': 'cta',
                'priority': 'medium',
                'message': 'Добавьте призыв к действию',
                'impact': '+40% к конверсии'
            })

        # Читаемость
        if quality_metrics['readability'] < 60:
            recommendations.append({
                'type': 'readability',
                'priority': 'high',
                'message': 'Упростите текст, используйте короткие предложения',
                'impact': '+20% к дочитываемости'
            })

        # Эмоциональность
        if 0.4 <= quality_metrics['emotional_score'] <= 0.6:
            recommendations.append({
                'type': 'emotion',
                'priority': 'low',
                'message': 'Добавьте эмоциональную окраску',
                'impact': '+15% к вовлечению'
            })

        # Сортируем по приоритету
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order[x['priority']])

        return recommendations[:5]  # Топ-5 рекомендаций

    def _calculate_overall_score(self, quality_metrics: Dict) -> float:
        """Расчет общей оценки качества"""
        score = 0.0

        for metric, weight in self.quality_weights.items():
            if metric in quality_metrics:
                score += quality_metrics[metric] * weight

        return round(score, 2)

    async def _predict_optimal_time(self, text: str, context: Optional[Dict] = None) -> Dict:
        """Предсказание оптимального времени публикации"""
        # Анализируем тип контента
        content_type = self._detect_content_type(text)

        # Оптимальное время по типу контента
        optimal_times = {
            'news': ['09:00', '12:00', '18:00'],
            'educational': ['10:00', '15:00', '20:00'],
            'entertainment': ['19:00', '21:00', '22:00'],
            'business': ['08:00', '11:00', '14:00'],
            'general': ['09:00', '15:00', '21:00']
        }

        # Дни недели
        best_days = {
            'news': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
            'educational': ['tuesday', 'wednesday', 'thursday'],
            'entertainment': ['friday', 'saturday', 'sunday'],
            'business': ['tuesday', 'wednesday', 'thursday'],
            'general': ['tuesday', 'wednesday', 'thursday', 'friday']
        }

        times = optimal_times.get(content_type, optimal_times['general'])
        days = best_days.get(content_type, best_days['general'])

        return {
            'recommended_times': times,
            'best_days': days,
            'content_type': content_type,
            'reasoning': f"Для контента типа '{content_type}' оптимальное время: {times[0]}"
        }

    def _detect_content_type(self, text: str) -> str:
        """Определение типа контента"""
        text_lower = text.lower()

        # Ключевые слова для разных типов
        news_keywords = ['сегодня', 'вчера', 'произошло', 'заявил', 'сообщает', 'новость']
        educational_keywords = ['узнайте', 'как', 'почему', 'совет', 'гайд', 'инструкция']
        entertainment_keywords = ['смешно', 'прикол', 'мем', 'видео', 'фото', 'лол']
        business_keywords = ['бизнес', 'деньги', 'инвестиции', 'стартап', 'доход', 'продажи']

        # Подсчет совпадений
        scores = {
            'news': sum(1 for kw in news_keywords if kw in text_lower),
            'educational': sum(1 for kw in educational_keywords if kw in text_lower),
            'entertainment': sum(1 for kw in entertainment_keywords if kw in text_lower),
            'business': sum(1 for kw in business_keywords if kw in text_lower)
        }

        # Определяем тип с максимальным счетом
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        return 'general'

    async def _save_analysis_result(self, text: str, result: Dict):
        """Сохранение результата анализа для обучения"""
        # Добавляем в историю
        self.content_history.append(text)

        # Ограничиваем размер истории
        if len(self.content_history) > 1000:
            self.content_history = self.content_history[-1000:]

        # Сохраняем в БД если доступна
        if self.db:
            try:
                await self.db.set_setting(
                    f'content_analysis_{datetime.now().timestamp()}',
                    json.dumps(result)
                )
            except Exception as e:
                logger.error(f"Ошибка сохранения анализа: {e}")

    def _get_default_analysis(self) -> Dict:
        """Возвращает анализ по умолчанию при ошибке"""
        return {
            'basic_metrics': {
                'text_length': 0,
                'word_count': 0,
                'emoji_count': 0,
                'hashtag_count': 0
            },
            'quality_metrics': {
                'readability': 50,
                'engagement_potential': 0.5,
                'uniqueness': 0.8
            },
            'performance_prediction': {
                'predicted_views': 100,
                'predicted_likes': 5,
                'predicted_engagement_rate': 5.0
            },
            'recommendations': [{
                'type': 'error',
                'priority': 'high',
                'message': 'Не удалось проанализировать контент',
                'impact': 'Неизвестно'
            }],
            'overall_score': 0.5,
            'error': True
        }

    async def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Пакетный анализ текстов"""
        results = []

        for text in texts:
            result = await self.analyze_content(text)
            results.append(result)
            await asyncio.sleep(0.1)  # Небольшая задержка

        return results

    async def compare_contents(self, text1: str, text2: str) -> Dict:
        """Сравнение двух текстов"""
        analysis1 = await self.analyze_content(text1)
        analysis2 = await self.analyze_content(text2)

        comparison = {
            'text1_score': analysis1['overall_score'],
            'text2_score': analysis2['overall_score'],
            'winner': 1 if analysis1['overall_score'] > analysis2['overall_score'] else 2,
            'score_difference': abs(analysis1['overall_score'] - analysis2['overall_score']),
            'key_differences': self._find_key_differences(analysis1, analysis2)
        }

        return comparison

    def _find_key_differences(self, analysis1: Dict, analysis2: Dict) -> List[str]:
        """Находит ключевые различия между анализами"""
        differences = []

        # Сравниваем основные метрики
        metrics_to_compare = [
            ('readability', 'Читаемость'),
            ('engagement_potential', 'Потенциал вовлечения'),
            ('emotional_score', 'Эмоциональность'),
            ('uniqueness', 'Уникальность')
        ]

        for metric_key, metric_name in metrics_to_compare:
            val1 = analysis1['quality_metrics'].get(metric_key, 0)
            val2 = analysis2['quality_metrics'].get(metric_key, 0)

            diff = abs(val1 - val2)
            if diff > 0.2:  # Значительная разница
                if val1 > val2:
                    differences.append(f"Текст 1 имеет лучшую {metric_name.lower()} (+{diff:.1%})")
                else:
                    differences.append(f"Текст 2 имеет лучшую {metric_name.lower()} (+{diff:.1%})")

        return differences[:3]  # Топ-3 различия