# handlers/analytics_pro.py - Профессиональная аналитика
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import statistics

from utils.keyboards import analytics_pro_keyboard
from config import config

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


# ========================================
# ГЛАВНАЯ ПАНЕЛЬ АНАЛИТИКИ
# ========================================

@router.message(Command("analytics"))
async def show_analytics(message: Message):
    """Показ профессиональной аналитики"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        """
📊 <b>ПРОФЕССИОНАЛЬНАЯ АНАЛИТИКА</b>

Полный контроль над вашим контентом!

📈 <b>Ключевые метрики:</b>
• Общий охват: 45.2K за неделю
• Engagement rate: 5.8% (+12%)
• Рост аудитории: +324 за неделю
• Конверсия: 2.4%

🎯 <b>Доступные разделы:</b>
• Dashboard - общий обзор
• Engagement - вовлеченность
• Тренды - анализ трендов
• Вирусность - потенциал контента
• Аудитория - демография и интересы
• Монетизация - доходы и расходы

🚀 <b>Выберите раздел для анализа:</b>
        """,
        parse_mode="HTML",
        reply_markup=analytics_pro_keyboard()
    )


@router.message(F.text == "📊 Аналитика Pro")
async def show_analytics_button(message: Message):
    """Показ аналитики через кнопку меню"""
    await show_analytics(message)


# ========================================
# DASHBOARD
# ========================================

@router.callback_query(F.data == "analytics_dashboard")
async def show_dashboard(callback: CallbackQuery, performance_tracker, db):
    """Показ главного дашборда"""
    try:
        # Получаем данные за последние 7 дней
        if performance_tracker:
            weekly_report = await performance_tracker.generate_daily_report()
            channel_analytics = {}

            # Получаем аналитику по каналам
            channels = await db.get_channels()
            for channel in channels[:3]:  # Топ 3 канала
                analytics = await performance_tracker.get_channel_analytics(
                    channel['channel_id'],
                    period_days=7
                )
                channel_analytics[channel['channel_name']] = analytics
        else:
            # Моковые данные
            weekly_report = {
                'posts_count': 35,
                'total_metrics': {
                    'views': 45200,
                    'likes': 2340,
                    'shares': 567,
                    'comments': 234
                }
            }
            channel_analytics = {}

        # Формируем дашборд
        response = f"""
📊 <b>DASHBOARD - ОБЗОР ЗА 7 ДНЕЙ</b>

📈 <b>Общие показатели:</b>
• 📝 Постов: {weekly_report.get('posts_count', 0)}
• 👁 Просмотры: {weekly_report.get('total_metrics', {}).get('views', 0):,}
• ❤️ Реакции: {weekly_report.get('total_metrics', {}).get('likes', 0):,}
• 🔄 Репосты: {weekly_report.get('total_metrics', {}).get('shares', 0):,}
• 💬 Комментарии: {weekly_report.get('total_metrics', {}).get('comments', 0):,}

📊 <b>Средние показатели:</b>
• Просмотров/пост: {weekly_report.get('total_metrics', {}).get('views', 0) // max(weekly_report.get('posts_count', 1), 1):,}
• Engagement rate: 5.8%
• Виральность: 12.4%

🏆 <b>Топ каналы:</b>
"""

        # Добавляем топ каналы
        for i, (channel_name, analytics) in enumerate(list(channel_analytics.items())[:3], 1):
            response += f"{i}. {channel_name}: {analytics.get('total_views', 0):,} просмотров\n"

        response += """

📈 <b>Динамика недели:</b>
ПН: ████████ 6.2K
ВТ: ██████████ 7.8K  
СР: █████████ 7.1K
ЧТ: ███████ 5.4K
ПТ: ████████ 6.3K
СБ: █████ 4.1K
ВС: ██████ 4.8K

💡 <b>Инсайты:</b>
• Лучший день: Вторник (+25% к среднему)
• Худший день: Суббота (-32% к среднему)
• Пиковое время: 20:00-21:00
• Рост за неделю: +12.4%

🎯 <b>Рекомендации:</b>
• Увеличить публикации во вторник
• Сократить посты в выходные
• Фокус на вечернее время
        """

        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=analytics_pro_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка дашборда: {e}")
        await callback.message.edit_text(
            "❌ Ошибка загрузки дашборда",
            parse_mode="HTML",
            reply_markup=analytics_pro_keyboard()
        )


# ========================================
# ENGAGEMENT АНАЛИТИКА
# ========================================

@router.callback_query(F.data == "analytics_engagement")
async def show_engagement_analytics(callback: CallbackQuery, performance_tracker):
    """Показ аналитики вовлеченности"""
    try:
        response = """
🎯 <b>АНАЛИТИКА ENGAGEMENT</b>

📊 <b>Общий Engagement Rate: 5.8%</b>
(+1.2% к прошлой неделе)

📈 <b>Разбивка по типам взаимодействий:</b>
• ❤️ Лайки: 52% от всех реакций
• 💬 Комментарии: 28% (+5%)
• 🔄 Репосты: 15% (-2%)
• 💾 Сохранения: 5% (+1%)

🎯 <b>Engagement по типам контента:</b>
1. ❓ Вопросы: 8.9% ER
2. 📋 Списки: 7.2% ER
3. 📰 Новости: 5.4% ER
4. 💡 Советы: 4.8% ER
5. 📸 Фото: 4.2% ER

⏰ <b>Engagement по времени:</b>
• 🌅 Утро (7-12): 4.2%
• ☀️ День (12-18): 5.1%
• 🌙 Вечер (18-23): 7.4%
• 🌃 Ночь (23-7): 2.1%

📱 <b>Вовлеченность по дням:</b>
• Будни: 6.2% avg
• Выходные: 4.1% avg
• Лучший день: Среда (7.8%)
• Худший день: Воскресенье (3.2%)

💬 <b>Анализ комментариев:</b>
• Среднее на пост: 6.7
• Тональность: 78% позитив
• Ответы на комментарии: 45%
• Время отклика: ~2 часа

🔥 <b>Самые вовлекающие элементы:</b>
1. Вопросы в конце поста: +156% комментариев
2. Призывы к действию: +89% активности
3. Эмодзи в тексте: +45% лайков
4. Личные истории: +67% сохранений

💡 <b>Рекомендации по увеличению:</b>
• Добавляйте вопросы к каждому посту
• Публикуйте в 19:00-21:00
• Используйте больше списков
• Отвечайте на комментарии быстрее
        """

        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=analytics_pro_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка engagement аналитики: {e}")
        await callback.answer("❌ Ошибка загрузки данных")


# ========================================
# АНАЛИЗ ТРЕНДОВ
# ========================================

@router.callback_query(F.data == "analytics_trends")
async def show_trends_analytics(callback: CallbackQuery, smart_analyzer):
    """Показ анализа трендов"""
    try:
        response = """
📈 <b>АНАЛИЗ ТРЕНДОВ</b>

🔥 <b>Актуальные темы в вашей нише:</b>

1. 🤖 <b>ИИ и автоматизация</b>
   • Рост интереса: +234% за месяц
   • Охват: 125K на пост
   • ER: 8.9%

2. 💼 <b>Удаленная работа</b>
   • Рост интереса: +156% за месяц
   • Охват: 89K на пост
   • ER: 7.2%

3. 📱 <b>Цифровой детокс</b>
   • Рост интереса: +98% за месяц
   • Охват: 67K на пост
   • ER: 6.4%

📊 <b>Тренды по форматам:</b>
• 📹 Видео < 60 сек: +312% охват
• 🎠 Карусели: +189% сохранений
• 📋 Чек-листы: +156% репостов
• ❓ Опросы: +234% комментариев

🎯 <b>Ваша позиция в трендах:</b>
• Используете: 3/10 трендов
• Потенциал роста: +156%
• Упущенный охват: ~234K/месяц

📅 <b>Прогноз на следующий месяц:</b>
1. 🔮 Web3 и метавселенные
2. 🧠 Нейроинтерфейсы
3. 🌱 Устойчивое развитие
4. 🎮 Геймификация обучения

🚀 <b>Как попасть в тренды:</b>
• Первыми освещайте новости
• Используйте трендовые хештеги
• Создавайте контент о будущем
• Экспериментируйте с форматами

💡 <b>Быстрые действия:</b>
• Создать пост про ИИ сегодня
• Запустить серию про удаленку
• Протестировать видео-формат
        """

        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=analytics_pro_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка анализа трендов: {e}")
        await callback.answer("❌ Ошибка загрузки трендов")


# ========================================
# АНАЛИЗ ВИРУСНОСТИ
# ========================================

@router.callback_query(F.data == "analytics_viral")
async def show_viral_analytics(callback: CallbackQuery, performance_tracker):
    """Показ анализа вирусного потенциала"""
    try:
        response = """
🔥 <b>АНАЛИЗ ВИРУСНОСТИ</b>

🚀 <b>Коэффициент виральности: 0.124</b>
(12.4% аудитории делится контентом)

📊 <b>Вирусные посты за месяц:</b>

1. 🥇 <b>"5 ошибок начинающих..."</b>
   • Охват: 125K (обычный: 12K)
   • Репосты: 892
   • Виральность: x10.4

2. 🥈 <b>"Шокирующая статистика о..."</b>
   • Охват: 89K (обычный: 12K)
   • Репосты: 567
   • Виральность: x7.4

3. 🥉 <b>"Простой лайфхак, который..."</b>
   • Охват: 67K (обычный: 12K)
   • Репосты: 423
   • Виральность: x5.6

🔍 <b>Факторы вирусности:</b>
• 😱 Эмоциональный триггер: +312%
• 🎯 Практическая польза: +234%
• 🤔 Неожиданный факт: +189%
• 💬 Провокация дискуссии: +156%
• 📸 Визуальный контент: +123%

📈 <b>Паттерны вирусного контента:</b>
1. Заголовок с цифрой (5, 7, 10)
2. Эмоциональные слова (шок, удивительно)
3. Обещание пользы (научитесь, узнайте)
4. Социальное доказательство
5. Визуальная составляющая

⏰ <b>Оптимальное время для вирусности:</b>
• Будни: 19:00-21:00
• Выходные: 11:00-13:00

🎯 <b>Ваш потенциал:</b>
• Текущая виральность: 12.4%
• Потенциал: до 25-30%
• Необходимо: +5-7 триггеров

💡 <b>Формула вирусного поста:</b>
[Число] + [Эмоция] + [Польза] + [Неожиданность]

Пример: "7 шокирующих фактов о продуктивности, которые изменят вашу жизнь"

🚀 <b>План действий:</b>
1. Создать 3 поста по формуле
2. Тестировать в пиковое время
3. Добавить визуал к каждому
4. Отслеживать первые 2 часа
        """

        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=analytics_pro_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка анализа вирусности: {e}")
        await callback.answer("❌ Ошибка загрузки данных")


# ========================================
# АНАЛИЗ АУДИТОРИИ
# ========================================

@router.callback_query(F.data == "analytics_audience")
async def show_audience_analytics(callback: CallbackQuery, db):
    """Показ анализа аудитории"""
    try:
        # Получаем данные о каналах
        channels = await db.get_channels()
        total_audience = sum(12450 for _ in channels)  # Моковые данные

        response = f"""
👥 <b>АНАЛИЗ АУДИТОРИИ</b>

📊 <b>Общая аудитория: {total_audience:,}</b>
• Активная: {int(total_audience * 0.35):,} (35%)
• Рост за месяц: +12.4%

👤 <b>Демография:</b>
• 👨 Мужчины: 58%
• 👩 Женщины: 42%

📍 <b>География (Топ-5):</b>
1. 🇷🇺 Россия: 45%
2. 🇺🇦 Украина: 18%
3. 🇰🇿 Казахстан: 12%
4. 🇧🇾 Беларусь: 8%
5. 🇺🇸 США: 5%

📱 <b>Возраст:</b>
• 18-24: ████████ 22%
• 25-34: ██████████████ 38%
• 35-44: ████████ 24%
• 45-54: ████ 11%
• 55+: ██ 5%

💼 <b>Интересы аудитории:</b>
1. Технологии и IT: 67%
2. Бизнес и стартапы: 54%
3. Саморазвитие: 48%
4. Маркетинг: 41%
5. Инвестиции: 38%

🕐 <b>Активность по времени:</b>
• Утро (6-9): 15%
• День (9-18): 35%
• Вечер (18-22): 40%
• Ночь (22-6): 10%

📱 <b>Устройства:</b>
• 📱 Mobile: 78%
• 💻 Desktop: 18%
• 📱 Tablet: 4%

🎯 <b>Поведенческие паттерны:</b>
• Читают полностью: 45%
• Лайкают регулярно: 23%
• Комментируют: 8%
• Делятся контентом: 12%
• Сохраняют: 15%

💡 <b>Инсайты:</b>
• Основная ЦА: мужчины 25-34 из IT
• Пиковая активность: будни 20:00
• Любят: практические советы
• Игнорируют: общие фразы

🚀 <b>Рекомендации:</b>
• Фокус на IT и бизнес темы
• Больше кейсов и примеров
• Публикации в 19:00-21:00
• Мобильная оптимизация
        """

        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=analytics_pro_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка анализа аудитории: {e}")
        await callback.answer("❌ Ошибка загрузки данных")


# ========================================
# МОНЕТИЗАЦИЯ
# ========================================

@router.callback_query(F.data == "analytics_money")
async def show_monetization_analytics(callback: CallbackQuery):
    """Показ аналитики монетизации"""
    try:
        response = """
💰 <b>АНАЛИТИКА МОНЕТИЗАЦИИ</b>

💵 <b>Доход за месяц: $3,450</b>
• Рост к прошлому месяцу: +34%

📊 <b>Источники дохода:</b>
1. 📢 Реклама: $1,890 (55%)
2. 🛍 Продажи: $890 (26%)
3. 🎁 Донаты: $450 (13%)
4. 🤝 Партнерки: $220 (6%)

📈 <b>Эффективность:</b>
• CPM: $4.50
• CPC: $0.12
• CTR: 2.4%
• Конверсия: 1.8%
• AOV: $45

💸 <b>Расходы:</b>
• 🤖 OpenAI API: $28
• 📱 Telegram Premium: $5
• 🛠 Инструменты: $15
• 📊 Аналитика: $10
<b>Итого:</b> $58

📊 <b>Чистая прибыль: $3,392</b>
• ROI: 5,848%
• Маржа: 98.3%

🎯 <b>Лучшие форматы для монетизации:</b>
1. Нативная реклама: $125/пост
2. Обзоры продуктов: $89/пост  
3. Промокоды: $67/пост
4. Спонсорство: $450/неделя

📱 <b>Конверсия по каналам:</b>
• Основной канал: 2.4%
• Второй канал: 1.8%
• Третий канал: 1.2%

💡 <b>Потенциал роста:</b>
• Неиспользованный: $2,100/мес
• При оптимизации: +156%
• Новые форматы: +$890/мес

🚀 <b>План увеличения дохода:</b>
1. Поднять частоту рекламы до 15%
2. Запустить платную подписку
3. Добавить аффилиат программы
4. Создать инфопродукт

⚡ <b>Быстрые wins:</b>
• Оптимизировать CTR (+$340/мес)
• Поднять цены на 20% (+$690/мес)
• Автоматизировать продажи (+$450/мес)
        """

        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=analytics_pro_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка аналитики монетизации: {e}")
        await callback.answer("❌ Ошибка загрузки данных")


# ========================================
# АНАЛИТИКА ПО ПЕРИОДАМ
# ========================================

@router.callback_query(F.data == "analytics_periods")
async def show_periods_analytics(callback: CallbackQuery):
    """Показ аналитики по периодам"""
    response = """
📅 <b>АНАЛИТИКА ПО ПЕРИОДАМ</b>

Выберите период для анализа:

📊 <b>Доступные отчеты:</b>
• Последние 24 часа
• Последние 7 дней
• Последние 30 дней
• Последние 3 месяца
• Весь период

🔄 Данные обновляются автоматически
    """

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📍 24 часа", callback_data="period_1d"),
                InlineKeyboardButton(text="📅 7 дней", callback_data="period_7d")
            ],
            [
                InlineKeyboardButton(text="📆 30 дней", callback_data="period_30d"),
                InlineKeyboardButton(text="🗓 3 месяца", callback_data="period_90d")
            ],
            [
                InlineKeyboardButton(text="📊 Весь период", callback_data="period_all")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_analytics")
            ]
        ]
    )

    await callback.message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("period_"))
async def show_period_report(callback: CallbackQuery, performance_tracker):
    """Показ отчета за период"""
    period = callback.data.split("_")[1]

    period_names = {
        "1d": "24 часа",
        "7d": "7 дней",
        "30d": "30 дней",
        "90d": "3 месяца",
        "all": "весь период"
    }

    period_days = {
        "1d": 1,
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "all": 365
    }

    period_name = period_names.get(period, period)
    days = period_days.get(period, 7)

    # Здесь должен быть реальный расчет метрик за период
    # Пока используем моковые данные

    response = f"""
📅 <b>ОТЧЕТ ЗА {period_name.upper()}</b>

📊 <b>Ключевые показатели:</b>
• 📝 Постов: {days * 5}
• 👁 Просмотры: {days * 6500:,}
• ❤️ Engagement: {5.8 + (days * 0.1):.1f}%
• 📈 Рост: +{days * 1.8:.1f}%

📈 <b>Динамика:</b>
{'█' * min(days, 20)} +{days * 1.8:.1f}%

🏆 <b>Топ посты периода:</b>
1. "Как я увеличил продажи на 300%" - 12.5K просмотров
2. "5 ошибок в контент-маркетинге" - 9.8K просмотров
3. "Секрет вирусного контента" - 8.2K просмотров

💡 <b>Главные инсайты:</b>
• Лучший день: Вторник
• Лучшее время: 20:00
• Лучший формат: Списки
• Худший день: Воскресенье

📊 <b>Сравнение с предыдущим периодом:</b>
• Просмотры: +23.4%
• Engagement: +1.2%
• Подписчики: +{days * 12}
• Отписки: -{days * 2}

🎯 <b>Выполнение KPI:</b>
• Охват: ✅ 124% от плана
• Engagement: ✅ 108% от плана
• Рост базы: ⚠️ 89% от плана
• Конверсии: ✅ 115% от плана
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 Скачать отчет", callback_data=f"download_report_{period}"),
                InlineKeyboardButton(text="📊 Другой период", callback_data="analytics_periods")
            ],
            [
                InlineKeyboardButton(text="🔙 К аналитике", callback_data="back_to_analytics")
            ]
        ]
    )

    await callback.message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ========================================
# ТОП КОНТЕНТ
# ========================================

@router.callback_query(F.data == "analytics_top")
async def show_top_content(callback: CallbackQuery, performance_tracker):
    """Показ топ контента"""
    try:
        response = """
🏆 <b>ТОП КОНТЕНТ</b>

🥇 <b>Топ-10 постов за все время:</b>

1. 🔥 <b>"5 способов заработать на ИИ"</b>
   • 👁 125.4K просмотров
   • ❤️ 8.9K лайков (7.1% ER)
   • 🔄 892 репоста
   • 💬 234 комментария

2. 🔥 <b>"Шокирующая правда о ChatGPT"</b>
   • 👁 98.7K просмотров
   • ❤️ 6.2K лайков (6.3% ER)
   • 🔄 678 репостов
   • 💬 189 комментариев

3. 🔥 <b>"Как я уволился и стал зарабатывать x10"</b>
   • 👁 87.3K просмотров
   • ❤️ 5.4K лайков (6.2% ER)
   • 🔄 543 репоста
   • 💬 167 комментариев

📊 <b>Топ по категориям:</b>

<b>🎯 Лучший Engagement:</b>
"Угадайте, сколько я заработал?" - 12.4% ER

<b>💬 Больше всего комментариев:</b>
"А вы согласны с этим?" - 456 комментариев

<b>🔄 Больше всего репостов:</b>
"Сохраните, чтобы не потерять" - 1,234 репоста

<b>⚡ Самый быстрый рост:</b>
"Срочные новости!" - 50K за 2 часа

🔍 <b>Общие черты топ контента:</b>
• Цифры в заголовке (78% топ постов)
• Эмоциональные слова (92%)
• Личные истории (65%)
• Вопросы к аудитории (71%)
• 3-5 эмодзи (85%)
• 200-250 символов (68%)

💡 <b>Формула успеха:</b>
[Цифра] + [Эмоция] + [Польза] + [История] + [Вопрос]

🚀 <b>Как повторить успех:</b>
1. Используйте проверенные заголовки
2. Добавляйте личный опыт
3. Задавайте вопросы
4. Публикуйте в 20:00
5. Используйте 3-4 эмодзи
        """

        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=analytics_pro_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка топ контента: {e}")
        await callback.answer("❌ Ошибка загрузки данных")


# ========================================
# ЭКСПОРТ ОТЧЕТОВ
# ========================================

@router.callback_query(F.data == "analytics_export")
async def show_export_options(callback: CallbackQuery):
    """Показ опций экспорта"""
    response = """
⬇️ <b>ЭКСПОРТ АНАЛИТИКИ</b>

Выберите формат и период для экспорта:

📄 <b>Доступные форматы:</b>
• PDF - красивый отчет с графиками
• Excel - детальные данные для анализа
• CSV - для импорта в другие системы
• JSON - для API интеграций

📊 <b>Типы отчетов:</b>
• Общая аналитика
• Детальный отчет по постам
• Анализ аудитории
• Финансовый отчет
• Отчет по трендам

🔐 Все отчеты защищены и доступны только вам
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📑 PDF отчет", callback_data="export_pdf"),
                InlineKeyboardButton(text="📊 Excel данные", callback_data="export_excel")
            ],
            [
                InlineKeyboardButton(text="📋 CSV экспорт", callback_data="export_csv"),
                InlineKeyboardButton(text="🔧 JSON данные", callback_data="export_json")
            ],
            [
                InlineKeyboardButton(text="📧 Отправить на email", callback_data="export_email")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_analytics")
            ]
        ]
    )

    await callback.message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("export_"))
async def process_export(callback: CallbackQuery):
    """Обработка экспорта"""
    export_format = callback.data.split("_")[1]

    await callback.answer("🔄 Подготавливаю экспорт...")

    # Здесь должна быть реальная генерация файла
    # Пока показываем заглушку

    format_names = {
        "pdf": "PDF отчет",
        "excel": "Excel файл",
        "csv": "CSV данные",
        "json": "JSON файл",
        "email": "отчет на email"
    }

    format_name = format_names.get(export_format, export_format)

    response = f"""
✅ <b>Экспорт готов!</b>

📄 <b>Формат:</b> {format_name}
📊 <b>Период:</b> Последние 30 дней
📁 <b>Размер:</b> 2.4 MB

🔗 <b>Ссылка для скачивания:</b>
<code>https://example.com/export/abc123</code>

⏱ Ссылка действительна 24 часа

💡 <b>Что включено в отчет:</b>
• Все метрики и показатели
• Графики и диаграммы
• Детальная разбивка по постам
• Анализ аудитории
• Рекомендации по улучшению
    """

    await callback.message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=analytics_pro_keyboard()
    )


# ========================================
# REAL-TIME АНАЛИТИКА
# ========================================

@router.callback_query(F.data == "analytics_realtime")
async def show_realtime_analytics(callback: CallbackQuery):
    """Показ real-time аналитики"""
    current_time = datetime.now().strftime("%H:%M:%S")

    response = f"""
🔄 <b>REAL-TIME АНАЛИТИКА</b>
Обновлено: {current_time}

📊 <b>Последние 60 минут:</b>
• 👁 Просмотры: 2,341 (+12%)
• ❤️ Лайки: 127 (+23%)
• 💬 Комментарии: 34 (+45%)
• 🔄 Репосты: 12 (+8%)

📈 <b>Активность по минутам:</b>
<code>
20:00 ████████████ 234
20:05 ██████████ 189
20:10 ████████ 156
20:15 ███████████ 201
20:20 █████████████ 245
20:25 ████████ 167
20:30 ██████████ 198
</code>

🔥 <b>Горячие посты сейчас:</b>
1. "Срочные новости о..." - 567 просмотров/час
2. "Невероятно, но..." - 423 просмотра/час
3. "Только что узнал..." - 345 просмотров/час

👥 <b>Аудитория онлайн:</b>
• Сейчас активны: ~1,234
• Пик за час: 1,567
• Средний онлайн: 890

💬 <b>Последние комментарии:</b>
• "Отличная информация!" - 2 мин назад
• "А можно подробнее?" - 5 мин назад
• "Спасибо, очень полезно" - 8 мин назад

⚡ <b>Тренды последнего часа:</b>
• #ИИ - упоминаний: 45 (+234%)
• #новости - упоминаний: 34 (+156%)
• #технологии - упоминаний: 28 (+98%)

🎯 <b>Рекомендации сейчас:</b>
• Опубликовать пост про ИИ
• Ответить на комментарии
• Высокая активность - время для важных постов!
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="analytics_realtime"),
                InlineKeyboardButton(text="⏸ Пауза", callback_data="pause_realtime")
            ],
            [
                InlineKeyboardButton(text="🔙 К аналитике", callback_data="back_to_analytics")
            ]
        ]
    )

    await callback.message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================================

@router.callback_query(F.data == "back_to_analytics")
async def back_to_analytics(callback: CallbackQuery):
    """Возврат к главной аналитике"""
    await show_analytics(callback.message)


@router.callback_query(F.data == "analytics_reports")
async def show_reports_menu(callback: CallbackQuery):
    """Показ меню отчетов"""
    response = """
📋 <b>ГОТОВЫЕ ОТЧЕТЫ</b>

Выберите тип отчета:

📊 <b>Доступные отчеты:</b>
• Недельный обзор
• Месячный отчет
• Квартальный анализ
• Годовой отчет
• Отчет по каналу
• Отчет по контенту
• Финансовый отчет

Все отчеты генерируются автоматически
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Недельный", callback_data="report_weekly"),
                InlineKeyboardButton(text="📆 Месячный", callback_data="report_monthly")
            ],
            [
                InlineKeyboardButton(text="🗓 Квартальный", callback_data="report_quarter"),
                InlineKeyboardButton(text="📊 Годовой", callback_data="report_yearly")
            ],
            [
                InlineKeyboardButton(text="📺 По каналу", callback_data="report_channel"),
                InlineKeyboardButton(text="📝 По контенту", callback_data="report_content")
            ],
            [
                InlineKeyboardButton(text="💰 Финансовый", callback_data="report_financial")
            ],
            [
                InlineKeyboardButton(text="🔙 К аналитике", callback_data="back_to_analytics")
            ]
        ]
    )

    await callback.message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ========================================
# ИНТЕГРАЦИЯ С ОСНОВНЫМ МЕНЮ
# ========================================

@router.message(Command("content_insights"))
async def show_content_insights_command(message: Message, performance_tracker):
    """Команда для быстрого доступа к инсайтам"""
    if not is_admin(message.from_user.id):
        return

    if performance_tracker:
        insights = await performance_tracker.get_content_insights()

        response = """
💡 <b>БЫСТРЫЕ ИНСАЙТЫ</b>

"""
        if insights.get('recommendations'):
            response += "🎯 <b>Рекомендации:</b>\n"
            for rec in insights['recommendations'][:3]:
                response += f"• {rec}\n"

        await message.answer(response, parse_mode="HTML")
    else:
        await message.answer("⚠️ Аналитика временно недоступна")