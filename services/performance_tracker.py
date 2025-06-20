# services/performance_tracker.py - Продвинутый трекер производительности
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json
import statistics

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Отслеживание и анализ производительности контента"""

    def __init__(self, db, bot=None):
        self.db = db
        self.bot = bot
        self.tracking_active = False

        # Кэш для метрик
        self.metrics_cache = defaultdict(dict)
        self.performance_history = []

        # Интервалы обновления
        self.update_intervals = {
            'realtime': 60,  # 1 минута
            'hourly': 3600,  # 1 час
            'daily': 86400,  # 24 часа
            'weekly': 604800  # 7 дней
        }

        logger.info("📊 Трекер производительности инициализирован")

    async def start_tracking(self):
        """Запуск отслеживания производительности"""
        if self.tracking_active:
            return

        self.tracking_active = True

        # Запускаем задачи отслеживания
        tasks = [
            asyncio.create_task(self._track_realtime_metrics()),
            asyncio.create_task(self._calculate_hourly_stats()),
            asyncio.create_task(self._generate_daily_reports()),
            asyncio.create_task(self._analyze_trends())
        ]

        logger.info("🚀 Отслеживание производительности запущено")

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("⏹ Отслеживание производительности остановлено")

    async def stop_tracking(self):
        """Остановка отслеживания"""
        self.tracking_active = False
        logger.info("⏹ Трекер производительности остановлен")

    async def track_post_performance(self, post_id: str, channel_id: str,
                                     content: str, timestamp: datetime) -> Dict:
        """Отслеживание производительности конкретного поста"""
        try:
            # Получаем метрики из Telegram
            metrics = await self._fetch_post_metrics(post_id, channel_id)

            # Сохраняем в кэш
            cache_key = f"{channel_id}_{post_id}"
            self.metrics_cache[cache_key] = {
                'post_id': post_id,
                'channel_id': channel_id,
                'content': content[:200],  # Сохраняем превью
                'timestamp': timestamp,
                'metrics': metrics,
                'last_update': datetime.now()
            }

            # Анализируем производительность
            performance_analysis = await self._analyze_post_performance(
                metrics, content, timestamp
            )

            # Сохраняем в БД
            await self._save_performance_data(
                post_id, channel_id, metrics, performance_analysis
            )

            return {
                'metrics': metrics,
                'analysis': performance_analysis,
                'status': 'tracked'
            }

        except Exception as e:
            logger.error(f"Ошибка отслеживания поста {post_id}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _fetch_post_metrics(self, post_id: str, channel_id: str) -> Dict:
        """Получение метрик поста из Telegram"""
        try:
            if not self.bot:
                # Возвращаем моковые данные для тестирования
                return {
                    'views': 150,
                    'likes': 12,
                    'shares': 3,
                    'comments': 5,
                    'engagement_rate': 8.0
                }

            # Здесь должен быть реальный код получения метрик через Telegram API
            # Пока возвращаем заглушку
            return {
                'views': 150,
                'likes': 12,
                'shares': 3,
                'comments': 5,
                'engagement_rate': 8.0
            }

        except Exception as e:
            logger.error(f"Ошибка получения метрик: {e}")
            return {}

    async def _analyze_post_performance(self, metrics: Dict, content: str,
                                        timestamp: datetime) -> Dict:
        """Анализ производительности поста"""
        # Базовая оценка
        performance_score = self._calculate_performance_score(metrics)

        # Сравнение с историческими данными
        historical_comparison = await self._compare_with_history(metrics)

        # Анализ времени публикации
        time_analysis = self._analyze_publication_time(timestamp, metrics)

        # Анализ контента
        content_factors = self._analyze_content_factors(content, metrics)

        # Определение категории производительности
        performance_category = self._categorize_performance(performance_score)

        return {
            'score': performance_score,
            'category': performance_category,
            'historical_comparison': historical_comparison,
            'time_analysis': time_analysis,
            'content_factors': content_factors,
            'insights': self._generate_insights(
                performance_score, historical_comparison,
                time_analysis, content_factors
            )
        }

    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Расчет общего балла производительности"""
        if not metrics:
            return 0.0

        views = metrics.get('views', 0)
        likes = metrics.get('likes', 0)
        shares = metrics.get('shares', 0)
        comments = metrics.get('comments', 0)

        if views == 0:
            return 0.0

        # Веса для разных метрик
        engagement_rate = ((likes + shares * 2 + comments * 3) / views) * 100

        # Нормализуем счет от 0 до 10
        if engagement_rate >= 20:
            score = 10.0
        elif engagement_rate >= 15:
            score = 9.0
        elif engagement_rate >= 10:
            score = 8.0
        elif engagement_rate >= 7:
            score = 7.0
        elif engagement_rate >= 5:
            score = 6.0
        elif engagement_rate >= 3:
            score = 5.0
        elif engagement_rate >= 2:
            score = 4.0
        elif engagement_rate >= 1:
            score = 3.0
        else:
            score = engagement_rate * 3  # Для очень низких значений

        return round(score, 1)

    async def _compare_with_history(self, metrics: Dict) -> Dict:
        """Сравнение с историческими данными"""
        # Получаем среднии исторические метрики
        historical_avg = await self._get_historical_averages()

        comparison = {}

        for metric_key in ['views', 'likes', 'shares', 'comments']:
            current_value = metrics.get(metric_key, 0)
            historical_value = historical_avg.get(metric_key, 0)

            if historical_value > 0:
                difference_percent = ((current_value - historical_value) / historical_value) * 100
                comparison[metric_key] = {
                    'current': current_value,
                    'average': historical_value,
                    'difference': round(difference_percent, 1),
                    'trend': 'up' if difference_percent > 0 else 'down' if difference_percent < 0 else 'stable'
                }
            else:
                comparison[metric_key] = {
                    'current': current_value,
                    'average': 0,
                    'difference': 0,
                    'trend': 'new'
                }

        return comparison

    async def _get_historical_averages(self) -> Dict:
        """Получение средних исторических показателей"""
        if not self.performance_history:
            # Возвращаем дефолтные значения
            return {
                'views': 100,
                'likes': 5,
                'shares': 1,
                'comments': 2
            }

        # Вычисляем средние значения из истории
        views_list = [item['metrics']['views'] for item in self.performance_history[-100:]
                      if 'views' in item.get('metrics', {})]
        likes_list = [item['metrics']['likes'] for item in self.performance_history[-100:]
                      if 'likes' in item.get('metrics', {})]
        shares_list = [item['metrics']['shares'] for item in self.performance_history[-100:]
                       if 'shares' in item.get('metrics', {})]
        comments_list = [item['metrics']['comments'] for item in self.performance_history[-100:]
                         if 'comments' in item.get('metrics', {})]

        return {
            'views': int(statistics.mean(views_list)) if views_list else 100,
            'likes': int(statistics.mean(likes_list)) if likes_list else 5,
            'shares': int(statistics.mean(shares_list)) if shares_list else 1,
            'comments': int(statistics.mean(comments_list)) if comments_list else 2
        }

    def _analyze_publication_time(self, timestamp: datetime, metrics: Dict) -> Dict:
        """Анализ времени публикации"""
        hour = timestamp.hour
        day_of_week = timestamp.strftime('%A').lower()

        # Оптимальные времена (на основе общих практик)
        optimal_hours = {
            'morning': (7, 9),
            'lunch': (12, 13),
            'evening': (19, 21)
        }

        # Определяем период дня
        if optimal_hours['morning'][0] <= hour <= optimal_hours['morning'][1]:
            time_period = 'morning'
            is_optimal = True
        elif optimal_hours['lunch'][0] <= hour <= optimal_hours['lunch'][1]:
            time_period = 'lunch'
            is_optimal = True
        elif optimal_hours['evening'][0] <= hour <= optimal_hours['evening'][1]:
            time_period = 'evening'
            is_optimal = True
        else:
            time_period = 'off-peak'
            is_optimal = False

        # Анализ дня недели
        weekday_performance = {
            'monday': 0.9,
            'tuesday': 1.1,
            'wednesday': 1.1,
            'thursday': 1.0,
            'friday': 0.95,
            'saturday': 0.8,
            'sunday': 0.75
        }

        day_multiplier = weekday_performance.get(day_of_week, 1.0)

        return {
            'hour': hour,
            'day_of_week': day_of_week,
            'time_period': time_period,
            'is_optimal_time': is_optimal,
            'day_performance_multiplier': day_multiplier,
            'recommendation': self._get_time_recommendation(hour, day_of_week, metrics)
        }

    def _get_time_recommendation(self, hour: int, day: str, metrics: Dict) -> str:
        """Получение рекомендации по времени публикации"""
        if 7 <= hour <= 9:
            return "Отличное время для утренней аудитории"
        elif 12 <= hour <= 13:
            return "Хорошее время для обеденного перерыва"
        elif 19 <= hour <= 21:
            return "Пиковое вечернее время"
        elif hour < 7:
            return "Слишком рано, попробуйте после 7:00"
        elif hour > 22:
            return "Слишком поздно, попробуйте до 22:00"
        else:
            return "Не самое оптимальное время, попробуйте утром или вечером"

    def _analyze_content_factors(self, content: str, metrics: Dict) -> Dict:
        """Анализ факторов контента, влияющих на производительность"""
        factors = {
            'length': len(content),
            'has_emoji': bool(re.search(r'[^\w\s,]', content)),
            'has_hashtags': '#' in content,
            'has_question': '?' in content,
            'has_call_to_action': any(cta in content.lower() for cta in
                                      ['подпис', 'лайк', 'коммент', 'поделись']),
            'has_link': 'http' in content or 'www.' in content
        }

        # Оценка влияния факторов
        positive_factors = []
        negative_factors = []

        if factors['has_emoji']:
            positive_factors.append("Использование эмодзи (+15% к engagement)")
        if factors['has_hashtags']:
            positive_factors.append("Наличие хештегов (+10% к охвату)")
        if factors['has_question']:
            positive_factors.append("Вопрос в тексте (+25% к комментариям)")
        if factors['has_call_to_action']:
            positive_factors.append("Призыв к действию (+20% к активности)")

        if factors['length'] > 500:
            negative_factors.append("Слишком длинный текст (-10% к дочитываемости)")
        if factors['length'] < 50:
            negative_factors.append("Слишком короткий текст (-15% к ценности)")
        if factors['has_link'] and metrics.get('views', 0) < 100:
            negative_factors.append("Ссылки могут снижать охват (-20%)")

        return {
            'factors': factors,
            'positive_factors': positive_factors,
            'negative_factors': negative_factors,
            'content_score': len(positive_factors) - len(negative_factors) * 0.5
        }

    def _categorize_performance(self, score: float) -> str:
        """Категоризация производительности"""
        if score >= 9:
            return "🔥 Вирусный"
        elif score >= 7:
            return "🎯 Отличный"
        elif score >= 5:
            return "✅ Хороший"
        elif score >= 3:
            return "📊 Средний"
        elif score >= 1:
            return "⚠️ Ниже среднего"
        else:
            return "❌ Плохой"

    def _generate_insights(self, score: float, historical: Dict,
                           time_analysis: Dict, content_factors: Dict) -> List[str]:
        """Генерация инсайтов на основе анализа"""
        insights = []

        # Инсайты по общей производительности
        if score >= 8:
            insights.append("🎉 Пост показал выдающиеся результаты!")
        elif score >= 6:
            insights.append("👍 Пост работает хорошо, продолжайте в том же духе")
        elif score < 4:
            insights.append("📈 Есть потенциал для улучшения")

        # Инсайты по сравнению с историей
        for metric, data in historical.items():
            if data['difference'] > 50:
                insights.append(f"🚀 {metric.capitalize()} выросли на {data['difference']}%!")
            elif data['difference'] < -30:
                insights.append(f"📉 {metric.capitalize()} упали на {abs(data['difference'])}%")

        # Инсайты по времени
        if not time_analysis['is_optimal_time']:
            insights.append("⏰ Попробуйте публиковать в пиковые часы (7-9, 12-13, 19-21)")

        # Инсайты по контенту
        if len(content_factors['positive_factors']) > 3:
            insights.append("✨ Отличная оптимизация контента!")
        elif len(content_factors['negative_factors']) > 1:
            insights.append("🔧 Контент можно улучшить")

        return insights[:5]  # Максимум 5 инсайтов

    async def _save_performance_data(self, post_id: str, channel_id: str,
                                     metrics: Dict, analysis: Dict):
        """Сохранение данных о производительности"""
        performance_data = {
            'post_id': post_id,
            'channel_id': channel_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'analysis': analysis
        }

        # Добавляем в историю
        self.performance_history.append(performance_data)

        # Ограничиваем размер истории
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

        # Сохраняем в БД
        if self.db:
            try:
                await self.db.set_setting(
                    f'performance_{post_id}',
                    json.dumps(performance_data)
                )
            except Exception as e:
                logger.error(f"Ошибка сохранения данных производительности: {e}")

    async def _track_realtime_metrics(self):
        """Отслеживание метрик в реальном времени"""
        while self.tracking_active:
            try:
                # Обновляем метрики для активных постов
                for cache_key, data in list(self.metrics_cache.items()):
                    if datetime.now() - data['last_update'] < timedelta(hours=24):
                        # Обновляем метрики для постов младше 24 часов
                        new_metrics = await self._fetch_post_metrics(
                            data['post_id'], data['channel_id']
                        )
                        data['metrics'] = new_metrics
                        data['last_update'] = datetime.now()

                await asyncio.sleep(self.update_intervals['realtime'])

            except Exception as e:
                logger.error(f"Ошибка отслеживания realtime метрик: {e}")
                await asyncio.sleep(60)

    async def _calculate_hourly_stats(self):
        """Расчет почасовой статистики"""
        while self.tracking_active:
            try:
                await asyncio.sleep(self.update_intervals['hourly'])

                # Агрегируем данные за последний час
                hourly_stats = await self._aggregate_hourly_data()

                # Сохраняем статистику
                if self.db:
                    await self.db.set_setting(
                        f'hourly_stats_{datetime.now().strftime("%Y%m%d%H")}',
                        json.dumps(hourly_stats)
                    )

            except Exception as e:
                logger.error(f"Ошибка расчета почасовой статистики: {e}")

    async def _generate_daily_reports(self):
        """Генерация ежедневных отчетов"""
        while self.tracking_active:
            try:
                await asyncio.sleep(self.update_intervals['daily'])

                # Генерируем отчет за день
                daily_report = await self.generate_daily_report()

                # Сохраняем отчет
                if self.db:
                    await self.db.set_setting(
                        f'daily_report_{datetime.now().strftime("%Y%m%d")}',
                        json.dumps(daily_report)
                    )

                # Отправляем уведомление админу
                if self.bot:
                    await self._send_daily_report_notification(daily_report)

            except Exception as e:
                logger.error(f"Ошибка генерации дневного отчета: {e}")

    async def _analyze_trends(self):
        """Анализ трендов производительности"""
        while self.tracking_active:
            try:
                await asyncio.sleep(self.update_intervals['weekly'])

                # Анализируем тренды за неделю
                trends = await self._calculate_weekly_trends()

                # Сохраняем анализ трендов
                if self.db:
                    await self.db.set_setting(
                        f'weekly_trends_{datetime.now().strftime("%Y%W")}',
                        json.dumps(trends)
                    )

            except Exception as e:
                logger.error(f"Ошибка анализа трендов: {e}")

    async def generate_daily_report(self) -> Dict:
        """Генерация подробного дневного отчета"""
        today = datetime.now().date()

        # Фильтруем данные за сегодня
        today_data = [
            item for item in self.performance_history
            if datetime.fromisoformat(item['timestamp']).date() == today
        ]

        if not today_data:
            return {
                'date': str(today),
                'posts_count': 0,
                'message': 'Нет данных за сегодня'
            }

        # Агрегируем метрики
        total_views = sum(item['metrics'].get('views', 0) for item in today_data)
        total_likes = sum(item['metrics'].get('likes', 0) for item in today_data)
        total_shares = sum(item['metrics'].get('shares', 0) for item in today_data)
        total_comments = sum(item['metrics'].get('comments', 0) for item in today_data)

        # Средние показатели
        avg_views = total_views // len(today_data) if today_data else 0
        avg_engagement = ((total_likes + total_shares + total_comments) / total_views * 100) if total_views > 0 else 0

        # Лучший и худший посты
        sorted_by_score = sorted(
            today_data,
            key=lambda x: x['analysis']['score'],
            reverse=True
        )

        best_post = sorted_by_score[0] if sorted_by_score else None
        worst_post = sorted_by_score[-1] if len(sorted_by_score) > 1 else None

        # Инсайты дня
        daily_insights = self._generate_daily_insights(today_data)

        return {
            'date': str(today),
            'posts_count': len(today_data),
            'total_metrics': {
                'views': total_views,
                'likes': total_likes,
                'shares': total_shares,
                'comments': total_comments
            },
            'average_metrics': {
                'views_per_post': avg_views,
                'engagement_rate': round(avg_engagement, 2)
            },
            'best_post': {
                'id': best_post['post_id'],
                'score': best_post['analysis']['score'],
                'content_preview': best_post.get('content', '')[:100]
            } if best_post else None,
            'worst_post': {
                'id': worst_post['post_id'],
                'score': worst_post['analysis']['score'],
                'content_preview': worst_post.get('content', '')[:100]
            } if worst_post else None,
            'insights': daily_insights,
            'recommendations': self._generate_daily_recommendations(today_data)
        }

    def _generate_daily_insights(self, today_data: List[Dict]) -> List[str]:
        """Генерация инсайтов дня"""
        insights = []

        # Анализ общей производительности
        avg_score = statistics.mean([item['analysis']['score'] for item in today_data])

        if avg_score >= 7:
            insights.append("🎉 Отличный день! Средний балл постов: {:.1f}/10".format(avg_score))
        elif avg_score >= 5:
            insights.append("✅ Хороший день. Средний балл: {:.1f}/10".format(avg_score))
        else:
            insights.append("📈 Есть потенциал для роста. Средний балл: {:.1f}/10".format(avg_score))

        # Анализ времени публикации
        optimal_times = sum(1 for item in today_data
                            if item['analysis']['time_analysis']['is_optimal_time'])

        if optimal_times < len(today_data) * 0.5:
            insights.append("⏰ Только {}% постов опубликованы в оптимальное время".format(
                int(optimal_times / len(today_data) * 100)
            ))

        # Анализ контента
        avg_positive_factors = statistics.mean([
            len(item['analysis']['content_factors']['positive_factors'])
            for item in today_data
        ])

        if avg_positive_factors >= 3:
            insights.append("✨ Отличная оптимизация контента!")
        elif avg_positive_factors < 2:
            insights.append("🔧 Контент можно улучшить добавлением эмодзи, хештегов и CTA")

        return insights

    def _generate_daily_recommendations(self, today_data: List[Dict]) -> List[str]:
        """Генерация рекомендаций на основе дневных данных"""
        recommendations = []

        # Анализ времени
        suboptimal_times = [
            item for item in today_data
            if not item['analysis']['time_analysis']['is_optimal_time']
        ]

        if len(suboptimal_times) > len(today_data) * 0.3:
            recommendations.append(
                "📅 Перенесите публикации на утро (7-9) или вечер (19-21)"
            )

        # Анализ контента
        low_engagement = [
            item for item in today_data
            if item['analysis']['score'] < 5
        ]

        if low_engagement:
            recommendations.append(
                "💡 Добавьте больше вопросов и призывов к действию"
            )

        # Анализ частоты
        if len(today_data) < 3:
            recommendations.append(
                "📈 Увеличьте частоту публикаций до 5-7 в день"
            )
        elif len(today_data) > 10:
            recommendations.append(
                "📉 Снизьте частоту публикаций для повышения качества"
            )

        return recommendations[:3]

    async def _aggregate_hourly_data(self) -> Dict:
        """Агрегация данных за час"""
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        hour_ago = current_hour - timedelta(hours=1)

        # Фильтруем данные за последний час
        hourly_data = [
            item for item in self.performance_history
            if hour_ago <= datetime.fromisoformat(item['timestamp']) < current_hour
        ]

        if not hourly_data:
            return {'hour': current_hour.isoformat(), 'posts': 0}

        return {
            'hour': current_hour.isoformat(),
            'posts': len(hourly_data),
            'total_views': sum(item['metrics'].get('views', 0) for item in hourly_data),
            'avg_score': statistics.mean([item['analysis']['score'] for item in hourly_data])
        }

    async def _calculate_weekly_trends(self) -> Dict:
        """Расчет недельных трендов"""
        # Данные за последнюю неделю
        week_ago = datetime.now() - timedelta(days=7)

        weekly_data = [
            item for item in self.performance_history
            if datetime.fromisoformat(item['timestamp']) > week_ago
        ]

        if not weekly_data:
            return {'message': 'Недостаточно данных для анализа трендов'}

        # Группируем по дням
        daily_scores = defaultdict(list)
        for item in weekly_data:
            day = datetime.fromisoformat(item['timestamp']).date()
            daily_scores[day].append(item['analysis']['score'])

        # Вычисляем средние баллы по дням
        daily_averages = {
            str(day): statistics.mean(scores)
            for day, scores in daily_scores.items()
        }

        # Определяем тренд
        scores_list = list(daily_averages.values())
        if len(scores_list) >= 3:
            first_half = statistics.mean(scores_list[:len(scores_list) // 2])
            second_half = statistics.mean(scores_list[len(scores_list) // 2:])

            if second_half > first_half * 1.1:
                trend = "growing"
                trend_description = "📈 Растущий тренд"
            elif second_half < first_half * 0.9:
                trend = "declining"
                trend_description = "📉 Снижающийся тренд"
            else:
                trend = "stable"
                trend_description = "➡️ Стабильный тренд"
        else:
            trend = "insufficient_data"
            trend_description = "❓ Недостаточно данных"

        return {
            'week_start': str(week_ago.date()),
            'week_end': str(datetime.now().date()),
            'daily_averages': daily_averages,
            'trend': trend,
            'trend_description': trend_description,
            'total_posts': len(weekly_data),
            'avg_weekly_score': statistics.mean([item['analysis']['score'] for item in weekly_data])
        }

    async def _send_daily_report_notification(self, report: Dict):
        """Отправка уведомления о дневном отчете"""
        if not self.bot:
            return

        try:
            from config import ADMIN_ID

            message = f"""
📊 <b>Ежедневный отчет производительности</b>

📅 <b>Дата:</b> {report['date']}
📝 <b>Постов опубликовано:</b> {report['posts_count']}

📈 <b>Общие показатели:</b>
• 👁 Просмотры: {report['total_metrics']['views']:,}
• ❤️ Лайки: {report['total_metrics']['likes']:,}
• 🔄 Репосты: {report['total_metrics']['shares']:,}
• 💬 Комментарии: {report['total_metrics']['comments']:,}

📊 <b>Средние показатели:</b>
• Просмотров на пост: {report['average_metrics']['views_per_post']:,}
• Engagement rate: {report['average_metrics']['engagement_rate']}%

💡 <b>Инсайты дня:</b>
{chr(10).join('• ' + insight for insight in report['insights'][:3])}

🎯 <b>Рекомендации:</b>
{chr(10).join('• ' + rec for rec in report['recommendations'][:3])}

Подробная аналитика: /analytics
            """

            await self.bot.send_message(
                chat_id=ADMIN_ID,
                text=message,
                parse_mode='HTML'
            )

        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")

    async def get_channel_analytics(self, channel_id: str, period_days: int = 7) -> Dict:
        """Получение аналитики по конкретному каналу"""
        since = datetime.now() - timedelta(days=period_days)

        # Фильтруем данные по каналу
        channel_data = [
            item for item in self.performance_history
            if item['channel_id'] == channel_id and
               datetime.fromisoformat(item['timestamp']) > since
        ]

        if not channel_data:
            return {
                'channel_id': channel_id,
                'period_days': period_days,
                'message': 'Нет данных за указанный период'
            }

        # Агрегируем метрики
        total_posts = len(channel_data)
        total_views = sum(item['metrics'].get('views', 0) for item in channel_data)
        total_engagement = sum(
            item['metrics'].get('likes', 0) +
            item['metrics'].get('shares', 0) +
            item['metrics'].get('comments', 0)
            for item in channel_data
        )

        avg_score = statistics.mean([item['analysis']['score'] for item in channel_data])

        # Лучшие посты
        top_posts = sorted(
            channel_data,
            key=lambda x: x['analysis']['score'],
            reverse=True
        )[:5]

        return {
            'channel_id': channel_id,
            'period_days': period_days,
            'total_posts': total_posts,
            'total_views': total_views,
            'total_engagement': total_engagement,
            'average_score': round(avg_score, 1),
            'engagement_rate': round((total_engagement / total_views * 100) if total_views > 0 else 0, 2),
            'top_posts': [
                {
                    'id': post['post_id'],
                    'score': post['analysis']['score'],
                    'views': post['metrics'].get('views', 0),
                    'content_preview': post.get('content', '')[:100]
                }
                for post in top_posts
            ]
        }

    async def get_content_insights(self) -> Dict:
        """Получение инсайтов по контенту"""
        if not self.performance_history:
            return {'message': 'Недостаточно данных для анализа'}

        # Анализируем факторы успешности
        successful_posts = [
            item for item in self.performance_history
            if item['analysis']['score'] >= 7
        ]

        unsuccessful_posts = [
            item for item in self.performance_history
            if item['analysis']['score'] < 4
        ]

        # Общие черты успешных постов
        success_factors = defaultdict(int)
        for post in successful_posts:
            for factor in post['analysis']['content_factors']['positive_factors']:
                success_factors[factor] += 1

        # Общие проблемы неуспешных постов
        failure_factors = defaultdict(int)
        for post in unsuccessful_posts:
            for factor in post['analysis']['content_factors']['negative_factors']:
                failure_factors[factor] += 1

        # Оптимальное время
        time_performance = defaultdict(list)
        for post in self.performance_history:
            hour = datetime.fromisoformat(post['timestamp']).hour
            time_performance[hour].append(post['analysis']['score'])

        best_hours = sorted(
            [(hour, statistics.mean(scores)) for hour, scores in time_performance.items()],
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return {
            'total_analyzed': len(self.performance_history),
            'success_rate': len(successful_posts) / len(
                self.performance_history) * 100 if self.performance_history else 0,
            'top_success_factors': [
                {'factor': factor, 'count': count}
                for factor, count in sorted(success_factors.items(), key=lambda x: x[1], reverse=True)[:5]
            ],
            'top_failure_factors': [
                {'factor': factor, 'count': count}
                for factor, count in sorted(failure_factors.items(), key=lambda x: x[1], reverse=True)[:5]
            ],
            'best_posting_hours': [
                {'hour': f"{hour}:00", 'avg_score': round(score, 1)}
                for hour, score in best_hours
            ],
            'recommendations': self._generate_content_recommendations(
                success_factors, failure_factors, time_performance
            )
        }

    def _generate_content_recommendations(self, success_factors: dict,
                                          failure_factors: dict,
                                          time_performance: dict) -> List[str]:
        """Генерация рекомендаций по контенту"""
        recommendations = []

        # Рекомендации по успешным факторам
        if success_factors:
            top_factor = max(success_factors, key=success_factors.get)
            recommendations.append(f"✅ Продолжайте использовать: {top_factor}")

        # Рекомендации по проблемам
        if failure_factors:
            top_problem = max(failure_factors, key=failure_factors.get)
            recommendations.append(f"❌ Избегайте: {top_problem}")

        # Рекомендации по времени
        if time_performance:
            best_hour = max(time_performance, key=lambda h: statistics.mean(time_performance[h]))
            recommendations.append(f"⏰ Лучшее время публикации: {best_hour}:00")

        # Общие рекомендации
        if len(self.performance_history) > 50:
            avg_score = statistics.mean([item['analysis']['score'] for item in self.performance_history])
            if avg_score < 5:
                recommendations.append("📈 Экспериментируйте с новыми форматами контента")
            elif avg_score > 7:
                recommendations.append("🎯 Отличная работа! Масштабируйте успешные подходы")

        return recommendations[:5]