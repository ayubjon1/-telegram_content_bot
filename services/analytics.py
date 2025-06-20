# handlers/analytics.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    from config import config
    return user_id == config.ADMIN_ID


@router.message(Command("smart_analysis"))
async def smart_content_analysis(message: Message):
    """Умный анализ контента"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🧠 <b>Умный анализ контента</b>\n\n"
        "Отправьте текст поста для анализа, и я предскажу его производительность:\n\n"
        "• 📊 Оценка качества\n"
        "• 📈 Предсказание engagement\n"
        "• 💡 Рекомендации по улучшению\n"
        "• ⏰ Оптимальное время публикации",
        parse_mode="HTML"
    )


@router.message(Command("test_analyzer"))
async def test_analyzer_command(message: Message, smart_analyzer=None):
    """Тест умного анализатора"""
    if not is_admin(message.from_user.id):
        return

    try:
        if not smart_analyzer:
            await message.answer("❌ ИИ-анализатор недоступен")
            return

        await message.answer("🧪 <b>Тестирую умный анализатор...</b>", parse_mode="HTML")

        # Тестовый контент
        test_content = """
🚀 Революция в мире искусственного интеллекта! 

Новая нейросеть ChatGPT показала невероятные результаты в анализе данных. 
Исследователи утверждают, что это прорыв в области автоматизации. 

А что вы думаете о будущем ИИ? 🤔

#искусственныйинтеллект #технологии #инновации
        """

        # Анализируем
        analysis = await smart_analyzer.analyze_content_quality(test_content)

        # Показываем результат
        await message.answer(
            f"✅ <b>Тест пройден успешно!</b>\n\n"
            f"🧠 <b>Умный анализатор работает!</b>\n"
            f"📊 Качество тестового контента: {analysis['quality_score']:.2f}/1.0\n"
            f"📈 Предсказание просмотров: ~{analysis['engagement_prediction']['predicted_views']}\n"
            f"💡 Рекомендаций: {len(analysis['recommendations'])}\n\n"
            f"Теперь отправьте любой текст длиннее 50 символов для анализа!",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка теста анализатора: {str(e)}")
        await message.answer(f"❌ Ошибка теста: {str(e)}")


@router.message(F.text & F.text.len() > 50)
async def analyze_content_text(message: Message, smart_analyzer=None):
    """Анализ присланного текста"""
    if not is_admin(message.from_user.id):
        return

    # Проверяем, что это не команда
    if message.text.startswith('/'):
        return

    try:
        if not smart_analyzer:
            await message.answer("❌ ИИ-анализатор недоступен")
            return

        await message.answer("🔄 <b>Анализирую контент...</b>", parse_mode="HTML")

        # Анализируем контент
        analysis = await smart_analyzer.analyze_content_quality(message.text)

        # Форматируем результат
        quality_emoji = "🟢" if analysis['quality_score'] > 0.7 else "🟡" if analysis['quality_score'] > 0.5 else "🔴"

        text = f"""
🧠 <b>Результат ИИ-анализа:</b>

{quality_emoji} <b>Общая оценка:</b> {analysis['quality_score']:.2f}/1.0

<b>📊 Предсказание engagement:</b>
• Просмотров: ~{analysis['engagement_prediction']['predicted_views']:,}
• Лайков: ~{analysis['engagement_prediction']['predicted_likes']:,}
• Репостов: ~{analysis['engagement_prediction']['predicted_shares']:,}
• Engagement rate: {analysis['engagement_prediction']['engagement_rate']:.2f}

<b>📈 Метрики контента:</b>
• Слов: {analysis['metrics']['word_count']}
• Читаемость: {analysis['metrics']['readability']:.0f}/100
• Эмодзи: {analysis['metrics']['emoji_count']}
• Хештеги: {analysis['metrics']['hashtag_count']}
• Трендовость: {analysis['trending_score']:.2f}/1.0

<b>⏰ Рекомендуемое время:</b> {analysis['optimal_posting_time']}

<b>💡 Рекомендации:</b>
        """

        for rec in analysis['recommendations']:
            text += f"\n• {rec}"

        if not analysis['recommendations']:
            text += "\n✅ Контент оптимизирован!"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка анализа: {str(e)}")
        await message.answer(f"❌ Ошибка анализа: {str(e)}")


@router.message(Command("analytics_help"))
async def analytics_help_command(message: Message):
    """Справка по командам аналитики"""
    if not is_admin(message.from_user.id):
        return

    help_text = """
🧠 <b>Справка по ИИ-аналитике</b>

<b>📊 Доступные команды:</b>
• <code>/smart_analysis</code> - запуск умного анализа
• <code>/test_analyzer</code> - тест анализатора
• <code>/analytics_help</code> - эта справка

<b>🔍 Как использовать:</b>
1. Отправьте <code>/smart_analysis</code>
2. Отправьте любой текст длиннее 50 символов
3. Получите детальный анализ и рекомендации

<b>📈 Что анализируется:</b>
• Качество контента (0-1.0)
• Предсказание engagement
• Оптимальное время публикации
• Рекомендации по улучшению

<b>💡 Метрики:</b>
• Количество слов, эмодзи, хештегов
• Читаемость текста
• Трендовость контента
• Вовлекающие элементы
    """

    await message.answer(help_text, parse_mode="HTML")