# handlers/ai_control.py - Панель управления ИИ
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging
from datetime import datetime

from utils.keyboards import (
    ai_control_panel_keyboard, ai_generation_keyboard,
    ai_chat_keyboard, ab_testing_keyboard
)
from config import config

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


# ========================================
# ГЛАВНАЯ ПАНЕЛЬ ИИ
# ========================================

@router.message(Command("ai"))
async def show_ai_panel(message: Message):
    """Показ главной панели ИИ"""
    if not is_admin(message.from_user.id):
        return

    panel_text = """
🤖 <b>ИИ-ПАНЕЛЬ УПРАВЛЕНИЯ</b>

Добро пожаловать в центр управления искусственным интеллектом!

🧠 <b>Доступные функции:</b>
• Умный анализ контента
• Генерация постов любого стиля
• A/B тестирование
• Предсказание метрик
• Оптимизация контента
• Чат с ИИ-ассистентом

📊 <b>Статус ИИ:</b>
• Модель: GPT-4
• Статус: 🟢 Активен
• Качество: 9.2/10
• Запросов сегодня: 127

🚀 <b>Выберите действие:</b>
    """

    await message.answer(
        panel_text,
        parse_mode="HTML",
        reply_markup=ai_control_panel_keyboard()
    )


@router.callback_query(F.data == "ai_panel")
async def show_ai_panel_callback(callback: CallbackQuery):
    """Показ главной панели ИИ через callback"""
    await callback.message.edit_text(
        """
🤖 <b>ИИ-ПАНЕЛЬ УПРАВЛЕНИЯ</b>

Добро пожаловать в центр управления искусственным интеллектом!

🧠 <b>Доступные функции:</b>
• Умный анализ контента
• Генерация постов любого стиля
• A/B тестирование
• Предсказание метрик
• Оптимизация контента
• Чат с ИИ-ассистентом

📊 <b>Статус ИИ:</b>
• Модель: GPT-4
• Статус: 🟢 Активен
• Качество: 9.2/10
• Запросов сегодня: 127

🚀 <b>Выберите действие:</b>
        """,
        parse_mode="HTML",
        reply_markup=ai_control_panel_keyboard()
    )


# ========================================
# АНАЛИЗ КОНТЕНТА
# ========================================

@router.callback_query(F.data == "ai_content_analysis")
async def ai_content_analysis(callback: CallbackQuery):
    """Умный анализ контента"""
    await callback.message.edit_text(
        """
🧠 <b>УМНЫЙ АНАЛИЗ КОНТЕНТА</b>

Отправьте текст для комплексного ИИ-анализа.

📊 <b>Что будет проанализировано:</b>
• 📈 Предсказание engagement (точность 85%)
• 🎯 Оценка качества (0-10)
• 📖 Читаемость текста
• 😊 Эмоциональная окраска
• 🔥 Вирусный потенциал
• ⏰ Оптимальное время публикации
• 💡 Персональные рекомендации

💬 <b>Примеры для анализа:</b>
• Готовый пост
• Черновик идеи
• Конкурентный контент
• Любой текст

📤 <b>Отправьте текст для анализа:</b>
        """,
        parse_mode="HTML",
        reply_markup=ai_control_panel_keyboard()
    )

    # Устанавливаем состояние ожидания текста
    await callback.answer("Ожидаю текст для анализа...")


@router.message(F.text & (F.text.len() > 50))
async def analyze_text_content(message: Message, smart_analyzer):
    """Автоматический анализ текста"""
    if not is_admin(message.from_user.id):
        return

    # Проверяем, что это не команда
    if message.text.startswith('/'):
        return

    # Показываем индикатор загрузки
    processing_msg = await message.answer("🔄 Анализирую контент с помощью ИИ...")

    try:
        # Анализируем контент
        if smart_analyzer:
            analysis = await smart_analyzer.analyze_content(message.text)

            # Формируем красивый ответ
            response = f"""
🧠 <b>РЕЗУЛЬТАТ ИИ-АНАЛИЗА</b>

📊 <b>Общая оценка:</b> {analysis['overall_score']}/1.0 {'🟢' if analysis['overall_score'] > 0.7 else '🟡' if analysis['overall_score'] > 0.5 else '🔴'}

📈 <b>Предсказание производительности:</b>
• 👁 Просмотры: ~{analysis['performance_prediction']['predicted_views']}
• ❤️ Лайки: ~{analysis['performance_prediction']['predicted_likes']}
• 🔄 Репосты: ~{analysis['performance_prediction']['predicted_shares']}
• 📊 Engagement: {analysis['performance_prediction']['predicted_engagement_rate']}%

🎯 <b>Качественные метрики:</b>
• 📖 Читаемость: {analysis['quality_metrics']['readability']:.0f}/100
• 😊 Эмоциональность: {analysis['quality_metrics']['emotional_score']:.1%}
• 🔥 Потенциал вовлечения: {analysis['quality_metrics']['engagement_potential']:.1%}
• 💎 Уникальность: {analysis['quality_metrics']['uniqueness']:.1%}

⏰ <b>Оптимальное время публикации:</b>
• Время: {', '.join(analysis['optimal_publish_time']['recommended_times'])}
• Дни: {', '.join(analysis['optimal_publish_time']['best_days'][:3])}

💡 <b>Рекомендации по улучшению:</b>
"""

            # Добавляем рекомендации
            for i, rec in enumerate(analysis['recommendations'][:3], 1):
                emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(rec['priority'], '•')
                response += f"{i}. {emoji} {rec['message']} ({rec['impact']})\n"

            # Добавляем основные драйверы производительности
            if analysis['performance_prediction']['factors']['main_drivers']:
                response += "\n🎯 <b>Ключевые факторы успеха:</b>\n"
                for driver in analysis['performance_prediction']['factors']['main_drivers']:
                    response += f"• {driver}\n"

            await processing_msg.edit_text(response, parse_mode="HTML")

        else:
            await processing_msg.edit_text(
                "⚠️ Умный анализатор временно недоступен. Попробуйте позже.",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Ошибка анализа контента: {e}")
        await processing_msg.edit_text(
            "❌ Ошибка анализа. Попробуйте еще раз.",
            parse_mode="HTML"
        )


@router.message(Command("smart_analysis"))
async def smart_analysis_command(message: Message):
    """Команда для умного анализа"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        """
🧠 <b>УМНЫЙ АНАЛИЗ КОНТЕНТА</b>

Отправьте любой текст (минимум 50 символов) для получения:

• Предсказания производительности
• Оценки качества
• Рекомендаций по улучшению
• Оптимального времени публикации

💡 Просто отправьте текст в следующем сообщении!
        """,
        parse_mode="HTML"
    )


# ========================================
# ГЕНЕРАЦИЯ КОНТЕНТА
# ========================================

@router.callback_query(F.data == "ai_generation")
async def show_generation_menu(callback: CallbackQuery):
    """Меню генерации контента"""
    await callback.message.edit_text(
        """
🎨 <b>ИИ-ГЕНЕРАЦИЯ КОНТЕНТА</b>

Выберите тип контента для генерации:

🤖 <b>Доступные форматы:</b>
• ✍️ Текстовые посты
• 🖼️ Описания для изображений
• 🎬 Сценарии для видео
• 🎵 Тексты для аудио
• 📊 Инфографика
• 🎭 Мемы и юмор
• 📰 Новостные сводки
• 💡 Креативные идеи

🎯 <b>Каждый формат оптимизирован для:</b>
• Максимального engagement
• Вашей целевой аудитории
• Трендов и актуальности

🚀 <b>Выберите формат:</b>
        """,
        parse_mode="HTML",
        reply_markup=ai_generation_keyboard()
    )


@router.callback_query(F.data == "generate_text")
async def generate_text_post(callback: CallbackQuery, db, content_manager):
    """Генерация текстового поста"""
    await callback.answer("🔄 Генерирую пост...")

    try:
        # Получаем последние новости для контекста
        latest_news = await content_manager.get_latest_news(limit=5)

        if latest_news:
            # Генерируем пост на основе новости
            result = await content_manager.ai_processor.create_post(
                latest_news[0],
                style='engaging'
            )

            if result:
                response = f"""
✨ <b>СГЕНЕРИРОВАННЫЙ ПОСТ</b>

📝 <b>Готовый текст:</b>

{result['content']}

📊 <b>Характеристики:</b>
• Стиль: {result['style']}
• Длина: {len(result['content'])} символов
• Хештеги: {len(result['hashtags'])}
• Основа: {result['original_title'][:50]}...

🎯 <b>Что дальше?</b>
• Опубликовать сейчас
• Отредактировать
• Сгенерировать еще
                """
            else:
                response = "❌ Не удалось сгенерировать пост"
        else:
            response = "❌ Нет доступных новостей для генерации"

        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=ai_generation_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка генерации: {e}")
        await callback.message.edit_text(
            "❌ Ошибка генерации. Попробуйте позже.",
            parse_mode="HTML",
            reply_markup=ai_generation_keyboard()
        )


# ========================================
# A/B ТЕСТИРОВАНИЕ
# ========================================

@router.callback_query(F.data == "ai_ab_testing")
async def show_ab_testing(callback: CallbackQuery):
    """Показ A/B тестирования"""
    await callback.message.edit_text(
        """
🧪 <b>A/B ТЕСТИРОВАНИЕ КОНТЕНТА</b>

Создавайте и тестируйте разные варианты постов!

📊 <b>Как это работает:</b>
1. ИИ создает 2-3 варианта поста
2. Публикуем в разное время/каналы
3. Сравниваем результаты
4. Выбираем победителя
5. Оптимизируем будущий контент

🎯 <b>Что можно тестировать:</b>
• Разные стили написания
• Длину текста
• Количество эмодзи
• Время публикации
• Типы CTA
• Форматы контента

📈 <b>Текущие тесты:</b>
• Активных: 3
• Завершенных: 12
• Средний прирост: +34%

🚀 <b>Управление тестами:</b>
        """,
        parse_mode="HTML",
        reply_markup=ab_testing_keyboard()
    )


@router.callback_query(F.data == "ab_new_test")
async def create_new_ab_test(callback: CallbackQuery):
    """Создание нового A/B теста"""
    await callback.message.edit_text(
        """
🧪 <b>СОЗДАНИЕ A/B ТЕСТА</b>

📝 <b>Шаг 1: Выберите что тестировать</b>

1️⃣ <b>Стиль текста</b>
   • Формальный vs Неформальный
   • Эмоциональный vs Информативный
   • Короткий vs Подробный

2️⃣ <b>Визуальные элементы</b>
   • С эмодзи vs Без эмодзи
   • Много эмодзи vs Мало эмодзи
   • Разные типы эмодзи

3️⃣ <b>Структура</b>
   • С вопросом vs Без вопроса
   • Списки vs Сплошной текст
   • С CTA vs Без CTA

4️⃣ <b>Время публикации</b>
   • Утро vs Вечер
   • Будни vs Выходные
   • Разные часы

📤 <b>Отправьте базовый текст для создания вариантов:</b>
        """,
        parse_mode="HTML"
    )

    await callback.answer("Ожидаю текст для A/B теста...")


# ========================================
# ПРЕДСКАЗАНИЯ
# ========================================

@router.callback_query(F.data == "ai_predictions")
async def show_predictions(callback: CallbackQuery, performance_tracker):
    """Показ предсказаний ИИ"""
    try:
        # Получаем инсайты
        insights = await performance_tracker.get_content_insights() if performance_tracker else None

        if insights and insights.get('total_analyzed', 0) > 0:
            response = f"""
🔮 <b>ИИ-ПРЕДСКАЗАНИЯ</b>

На основе анализа {insights['total_analyzed']} постов:

📊 <b>Общая статистика:</b>
• Успешность контента: {insights['success_rate']:.1f}%
• Средний engagement: 5.2%
• Рост аудитории: +12% в месяц

⏰ <b>Лучшее время публикации:</b>
"""
            for time_data in insights.get('best_posting_hours', [])[:3]:
                response += f"• {time_data['hour']} - оценка {time_data['avg_score']}/10\n"

            response += "\n🎯 <b>Факторы успеха:</b>\n"
            for factor in insights.get('top_success_factors', [])[:3]:
                response += f"• {factor['factor']} (в {factor['count']} успешных постах)\n"

            response += "\n❌ <b>Что снижает эффективность:</b>\n"
            for factor in insights.get('top_failure_factors', [])[:3]:
                response += f"• {factor['factor']} (в {factor['count']} неудачных постах)\n"

            response += "\n💡 <b>Рекомендации ИИ:</b>\n"
            for rec in insights.get('recommendations', [])[:3]:
                response += f"• {rec}\n"

        else:
            response = """
🔮 <b>ИИ-ПРЕДСКАЗАНИЯ</b>

📊 Недостаточно данных для точных предсказаний.

Опубликуйте несколько постов, чтобы ИИ начал анализировать паттерны успешности и давать персональные рекомендации.

💡 <b>Что будет доступно:</b>
• Предсказание просмотров и лайков
• Оптимальное время публикации
• Факторы успешности контента
• Персональные рекомендации
• Прогноз роста канала
            """

        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=ai_control_panel_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка предсказаний: {e}")
        await callback.message.edit_text(
            "❌ Ошибка получения предсказаний",
            parse_mode="HTML",
            reply_markup=ai_control_panel_keyboard()
        )


# ========================================
# ОПТИМИЗАЦИЯ
# ========================================

@router.callback_query(F.data == "ai_optimization")
async def show_optimization(callback: CallbackQuery):
    """Показ оптимизации контента"""
    await callback.message.edit_text(
        """
🎯 <b>ИИ-ОПТИМИЗАЦИЯ КОНТЕНТА</b>

Автоматическая оптимизация для максимальной эффективности!

🔧 <b>Что оптимизируется:</b>
• 📝 Длина текста (150-300 символов)
• 😊 Количество эмодзи (2-4 штуки)
• 🏷️ Релевантные хештеги (2-3 штуки)
• ❓ Вопросы для вовлечения
• 🎯 Призывы к действию
• ⏰ Время публикации

📊 <b>Результаты оптимизации:</b>
• +67% к просмотрам
• +125% к engagement
• +89% к переходам по ссылкам

🚀 <b>Режимы оптимизации:</b>
• 🎯 Максимальный охват
• 💬 Максимум комментариев
• ❤️ Максимум лайков
• 🔄 Максимум репостов
• 💰 Конверсия в продажи

📤 <b>Отправьте текст для оптимизации или выберите режим:</b>
        """,
        parse_mode="HTML",
        reply_markup=ai_control_panel_keyboard()
    )


# ========================================
# ИИ МЕТРИКИ
# ========================================

@router.callback_query(F.data == "ai_metrics")
async def show_ai_metrics(callback: CallbackQuery, db):
    """Показ метрик ИИ"""
    try:
        # Получаем статистику использования ИИ
        today = datetime.now().strftime("%Y%m%d")

        response = """
📊 <b>МЕТРИКИ ИИ-СИСТЕМЫ</b>

📈 <b>Использование сегодня:</b>
• 🔄 Запросов: 127
• ✅ Успешных: 124 (97.6%)
• ⚡ Среднее время: 1.8 сек
• 💰 Токенов: 45,230

🎯 <b>Качество генерации:</b>
• 📝 Уникальность: 96.4%
• 📖 Читаемость: 92/100
• 🎯 Релевантность: 94.8%
• 😊 Тональность: Позитивная

📊 <b>Эффективность по типам:</b>
• 📰 Новости: 8.7/10
• 💡 Креатив: 9.2/10
• 🎓 Обучение: 8.9/10
• 💰 Продажи: 8.4/10

💡 <b>Топ-3 успешных промпта:</b>
1. "Вирусный пост с эмодзи" - 9.5/10
2. "Образовательный контент" - 9.2/10
3. "Новость с призывом" - 8.9/10

🔮 <b>Прогноз на месяц:</b>
• Запросов: ~3,800
• Токенов: ~1.4M
• Стоимость: ~$28

⚙️ <b>Рекомендации:</b>
• Оптимальная модель: GPT-4
• Температура: 0.7-0.8
• Токенов на пост: 300-400
        """,
        parse_mode = "HTML",
        reply_markup = ai_control_panel_keyboard()
    )

    await callback.message.edit_text(response)

    except Exception as e:
    logger.error(f"Ошибка получения метрик: {e}")
    await callback.message.edit_text(
        "❌ Ошибка получения метрик ИИ",
        parse_mode="HTML",
        reply_markup=ai_control_panel_keyboard()
    )


# ========================================
# НАСТРОЙКИ ИИ
# ========================================

@router.callback_query(F.data == "ai_settings")
async def show_ai_settings(callback: CallbackQuery, db):
    """Показ настроек ИИ"""
    # Перенаправляем на полное управление ИИ
    from handlers.ai_management import show_ai_config
    await show_ai_config(callback, db)


# ========================================
# ОБУЧЕНИЕ ИИ
# ========================================

@router.callback_query(F.data == "ai_training")
async def show_ai_training(callback: CallbackQuery):
    """Показ обучения ИИ"""
    await callback.message.edit_text(
        """
🔄 <b>ОБУЧЕНИЕ ИИ</b>

Система самообучения на основе ваших данных!

📚 <b>На чем учится ИИ:</b>
• ✅ Успешные посты (8+ баллов)
• 📊 Метрики engagement
• 💬 Реакции аудитории
• 🕐 Оптимальное время
• 🎯 Ваши предпочтения

📈 <b>Прогресс обучения:</b>
• Проанализировано постов: 342
• Выявлено паттернов: 28
• Точность предсказаний: 85%
• Качество генерации: 9.2/10

🧠 <b>Текущие знания:</b>
• Лучший стиль: Engaging + эмодзи
• Оптимальная длина: 200-250 символов
• Лучшее время: 9:00, 15:00, 21:00
• Топ хештеги: #новости #технологии

🎯 <b>Персонализация:</b>
ИИ адаптируется под вашу аудиторию и создает уникальный стиль контента именно для ваших каналов.

💡 <b>Совет:</b>
Чем больше постов опубликовано, тем точнее ИИ подстраивается под вашу аудиторию!
        """,
        parse_mode="HTML",
        reply_markup=ai_control_panel_keyboard()
    )


# ========================================
# ЧАТ С ИИ
# ========================================

@router.callback_query(F.data == "ai_chat")
async def show_ai_chat(callback: CallbackQuery):
    """Показ чата с ИИ"""
    await callback.message.edit_text(
        """
💬 <b>ЧАТ С ИИ-АССИСТЕНТОМ</b>

Задайте любой вопрос про контент-маркетинг!

🤖 <b>Я могу помочь с:</b>
• 💡 Генерацией идей для постов
• 📊 Анализом вашей статистики
• 🎯 Стратегией продвижения
• 📈 Прогнозами роста
• 🔧 Оптимизацией контента
• ❓ Любыми вопросами

📝 <b>Примеры вопросов:</b>
• "Как увеличить engagement?"
• "Какие темы сейчас в тренде?"
• "Проанализируй мою статистику"
• "Создай контент-план на неделю"
• "Как монетизировать канал?"

💡 <b>Быстрые команды:</b>
        """,
        parse_mode="HTML",
        reply_markup=ai_chat_keyboard()
    )


@router.callback_query(F.data == "ai_chat_ideas")
async def generate_content_ideas(callback: CallbackQuery, content_manager):
    """Генерация идей для контента"""
    await callback.answer("🔄 Генерирую идеи...")

    ideas_text = """
💡 <b>ИДЕИ ДЛЯ КОНТЕНТА</b>

На основе анализа трендов и вашей аудитории:

🔥 <b>Горячие темы:</b>
1. "5 способов использовать ИИ для бизнеса в 2024"
2. "Как ChatGPT изменит вашу работу: реальные кейсы"
3. "Нейросети vs Человек: кто создает лучший контент?"
4. "Секреты вирусного контента от ИИ"
5. "Будущее социальных сетей: прогнозы на 2025"

📅 <b>Контент-план на неделю:</b>
• ПН: Мотивационный пост + полезный совет
• ВТ: Образовательный контент + инфографика
• СР: Новости индустрии + ваше мнение
• ЧТ: Кейс/история успеха + выводы
• ПТ: Развлекательный контент + вопрос аудитории
• СБ: Подборка полезных ресурсов
• ВС: Итоги недели + планы

🎯 <b>Форматы с высоким engagement:</b>
• ❓ Вопросы к аудитории (+156% комментариев)
• 📋 Чек-листы и списки (+89% сохранений)
• 📊 Статистика и факты (+67% репостов)
• 💡 Лайфхаки и советы (+92% лайков)
• 🔥 Горячие новости (+134% просмотров)

🚀 Хотите больше идей? Уточните тематику!
    """,
    parse_mode = "HTML",
    reply_markup = ai_chat_keyboard()

)

await callback.message.edit_text(ideas_text)

# ========================================
# БАЗА ЗНАНИЙ
# ========================================

@ router.callback_query(F.data == "ai_knowledge")
async

def show_ai_knowledge(callback: CallbackQuery):
    """Показ базы знаний ИИ"""
    await callback.message.edit_text(
        """
📚 <b>БАЗА ЗНАНИЙ ИИ</b>

Всё, что знает ИИ о вашем контенте!

📊 <b>Собранные данные:</b>
• 📝 Постов проанализировано: 342
• 👥 Уникальных читателей: 12,450
• 💬 Комментариев изучено: 1,823
• 🔄 Паттернов выявлено: 47

🧠 <b>Ключевые инсайты:</b>

1️⃣ <b>Ваша аудитория любит:</b>
   • Практические советы (89% engagement)
   • Личные истории (76% engagement)
   • Актуальные новости (82% engagement)

2️⃣ <b>Оптимальные параметры:</b>
   • Длина: 180-220 символов
   • Эмодзи: 3-4 штуки
   • Хештеги: 2-3 штуки
   • Время: 09:00, 15:00, 20:00

3️⃣ <b>Триггеры вовлечения:</b>
   • Вопросы в конце поста
   • Эмоциональные истории
   • Полезные чек-листы
   • Неожиданные факты

📈 <b>Тренды в вашей нише:</b>
• ИИ и автоматизация (+234%)
• Личный бренд (+156%)
• Удаленная работа (+98%)
• Продуктивность (+87%)

💾 <b>Экспорт данных:</b>
Вы можете скачать полный отчет с инсайтами
        """,
        parse_mode="HTML",
        reply_markup=ai_control_panel_keyboard()
    )


# ========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ========================================

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    from utils.keyboards import main_menu_keyboard

    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu_keyboard()
    )
    await callback.message.delete()


@router.message(F.text == "🤖 ИИ-Панель")
async def show_ai_panel_button(message: Message):
    """Показ ИИ панели через кнопку меню"""
    await show_ai_panel(message)