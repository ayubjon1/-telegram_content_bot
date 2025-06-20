# handlers/admin.py - УПРОЩЕННАЯ РАБОЧАЯ ВЕРСИЯ
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramAPIError
import logging
import re

from utils.keyboards import main_menu_keyboard
from config import config

logger = logging.getLogger(__name__)
router = Router()


class ChannelStates(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_channel_name = State()
    waiting_for_posts_per_day = State()


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Команда запуска бота"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return

    await state.clear()

    welcome_text = f"""
🤖 <b>Content Manager Bot v3.0.1</b>

✅ <b>Бот успешно запущен!</b>
✅ База данных работает
✅ Все системы готовы

🎯 <b>Основные функции:</b>
• Управление каналами
• Обработка новостей через ИИ
• Автоматическое планирование
• Система мониторинга

🚀 <b>Команды:</b>
• /add_channel - добавить канал
• /list_channels - список каналов
• /test_post - тестовый пост
• /status - статус системы
• /health_check - диагностика

Используйте меню ниже для управления:
    """

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


@router.message(Command("status"))
async def status_command(message: Message, db, scheduler, monitor):
    """Статус системы"""
    if not is_admin(message.from_user.id):
        return

    try:
        # Получаем базовую информацию
        channels = await db.get_channels()
        sources = await db.get_news_sources()

        scheduler_status = "🟢 Работает" if scheduler and scheduler.running else "🔴 Остановлен"
        monitor_status = "🟢 Активен" if monitor and monitor.running else "🔴 Неактивен"

        status_text = f"""
📊 <b>СТАТУС СИСТЕМЫ</b>

🏢 <b>Основные компоненты:</b>
• 📅 Планировщик: {scheduler_status}
• 🔍 Мониторинг: {monitor_status}
• 🗄️ База данных: 🟢 Работает
• 🤖 OpenAI API: {'🟢 Настроен' if config.OPENAI_API_KEY else '🔴 Не настроен'}

📊 <b>Ресурсы:</b>
• 📺 Каналов: {len(channels)}
• 📰 Источников: {len(sources)}
• 📈 Задач планировщика: {len(scheduler.jobs) if scheduler else 0}

⏰ <b>Время работы:</b> Активен
🔧 <b>Версия:</b> 3.0.1-fixed
        """

        await message.answer(status_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        await message.answer(f"❌ Ошибка получения статуса: {str(e)}")


@router.message(Command("health_check"))
async def health_check_command(message: Message, db, scheduler, monitor):
    """Полная диагностика системы"""
    if not is_admin(message.from_user.id):
        return

    await message.answer("🔍 <b>Выполняется диагностика...</b>", parse_mode="HTML")

    checks = []
    issues = []

    # Проверка базы данных
    try:
        await db.get_setting('test')
        checks.append("✅ База данных: Работает")
    except Exception as e:
        issues.append(f"❌ База данных: {str(e)}")

    # Проверка планировщика
    if scheduler and scheduler.running:
        checks.append(f"✅ Планировщик: Работает ({len(scheduler.jobs)} задач)")
    else:
        issues.append("❌ Планировщик: Не работает")

    # Проверка мониторинга
    if monitor and monitor.running:
        checks.append("✅ Мониторинг: Активен")
    else:
        issues.append("❌ Мониторинг: Неактивен")

    # Проверка OpenAI
    if config.OPENAI_API_KEY:
        checks.append("✅ OpenAI API: Ключ настроен")
    else:
        issues.append("❌ OpenAI API: Ключ не настроен")

    # Проверка каналов
    try:
        channels = await db.get_channels()
        if channels:
            active_channels = len([ch for ch in channels if ch['is_active']])
            checks.append(f"✅ Каналы: {active_channels} активных из {len(channels)}")
        else:
            issues.append("⚠️ Каналы: Не добавлены")
    except Exception as e:
        issues.append(f"❌ Каналы: Ошибка проверки")

    # Формируем отчет
    health_score = len(checks) / (len(checks) + len(issues)) * 100 if (checks or issues) else 0

    if health_score >= 80:
        status_emoji = "🟢"
        status_text = "ОТЛИЧНО"
    elif health_score >= 60:
        status_emoji = "🟡"
        status_text = "ХОРОШО"
    else:
        status_emoji = "🔴"
        status_text = "ПРОБЛЕМЫ"

    result_text = f"""
{status_emoji} <b>ДИАГНОСТИКА ЗАВЕРШЕНА</b>

📊 <b>Общий статус:</b> {status_text} ({health_score:.0f}%)

✅ <b>Работает корректно:</b>
{chr(10).join(checks) if checks else "• Нет исправных компонентов"}

❌ <b>Требует внимания:</b>
{chr(10).join(issues) if issues else "• Все компоненты в порядке"}

💡 <b>Рекомендации:</b>
"""

    if not config.OPENAI_API_KEY:
        result_text += "\n• Настройте OPENAI_API_KEY для ИИ функций"
    if not channels:
        result_text += "\n• Добавьте каналы для публикации"
    if health_score >= 80:
        result_text += "\n🎉 Система работает отлично!"

    await message.answer(result_text, parse_mode="HTML")


@router.message(Command("add_channel"))
async def start_add_channel(message: Message, state: FSMContext):
    """Начало добавления канала"""
    if not is_admin(message.from_user.id):
        return

    await state.set_state(ChannelStates.waiting_for_channel_id)

    await message.answer(
        "📺 <b>Добавление канала</b>\n\n"
        "Отправьте ID канала:\n"
        "• <code>@channel_username</code> (для публичных)\n"
        "• <code>-100xxxxxxxxx</code> (для приватных)\n\n"
        "❗️ <b>Важно:</b> Бот должен быть администратором канала!",
        parse_mode="HTML"
    )


@router.message(StateFilter(ChannelStates.waiting_for_channel_id))
async def process_channel_id(message: Message, state: FSMContext, bot: Bot, db):
    """Обработка ID канала"""
    if not is_admin(message.from_user.id):
        return

    channel_id = message.text.strip()

    if not (channel_id.startswith('@') or channel_id.startswith('-100')):
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Используйте @channel_username или -100xxxxxxxxx",
            parse_mode="HTML"
        )
        return

    try:
        # Проверяем доступ к каналу
        chat = await bot.get_chat(channel_id)
        bot_member = await bot.get_chat_member(channel_id, bot.id)

        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                "❌ <b>Нет прав администратора</b>\n\n"
                "Добавьте бота как администратора с правами на отправку сообщений.",
                parse_mode="HTML"
            )
            return

        # Сохраняем канал
        channel_name = chat.title or chat.username or 'Без названия'
        await db.add_channel(channel_id, channel_name, 5)  # 5 постов в день по умолчанию

        await state.clear()

        await message.answer(
            f"✅ <b>Канал добавлен!</b>\n\n"
            f"<b>Название:</b> {channel_name}\n"
            f"<b>ID:</b> <code>{channel_id}</code>\n"
            f"<b>Постов в день:</b> 5\n\n"
            f"Канал готов к работе!",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )

    except TelegramAPIError as e:
        logger.error(f"Ошибка доступа к каналу: {e}")
        await message.answer(
            "❌ <b>Ошибка доступа к каналу</b>\n\n"
            "Проверьте правильность ID и права бота.",
            parse_mode="HTML"
        )


@router.message(Command("list_channels"))
async def list_channels(message: Message, db):
    """Список каналов"""
    if not is_admin(message.from_user.id):
        return

    try:
        channels = await db.get_channels()

        if not channels:
            await message.answer(
                "📺 <b>Каналы не найдены</b>\n\n"
                "Используйте /add_channel для добавления.",
                parse_mode="HTML"
            )
            return

        text = "📺 <b>Ваши каналы:</b>\n\n"
        for i, channel in enumerate(channels, 1):
            status = "✅" if channel['is_active'] else "❌"
            text += f"<b>{i}. {channel['channel_name']}</b>\n"
            text += f"   ID: <code>{channel['channel_id']}</code>\n"
            text += f"   Статус: {status}\n"
            text += f"   Постов в день: {channel['posts_per_day']}\n\n"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка получения каналов: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("test_post"))
async def test_post_command(message: Message, bot: Bot, db):
    """Тестовый пост"""
    if not is_admin(message.from_user.id):
        return

    # Парсим команду
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ <b>Формат:</b> <code>/test_post @channel</code>",
            parse_mode="HTML"
        )
        return

    channel_id = parts[1]

    try:
        test_text = """
🧪 <b>Тестовый пост от Content Manager Bot</b>

✅ Если видите это сообщение - бот настроен правильно!

<b>Проверено:</b>
• Подключение к каналу ✅
• Права на отправку ✅
• Форматирование ✅

🤖 Готов к автоматическим публикациям!

#тест #готово
        """

        sent_message = await bot.send_message(
            chat_id=channel_id,
            text=test_text,
            parse_mode="HTML"
        )

        await message.answer(
            f"✅ <b>Тест успешен!</b>\n\n"
            f"Пост отправлен в {channel_id}\n"
            f"ID сообщения: {sent_message.message_id}",
            parse_mode="HTML"
        )

    except TelegramAPIError as e:
        logger.error(f"Ошибка тестового поста: {e}")
        await message.answer(
            f"❌ <b>Ошибка отправки</b>\n\n"
            f"Проверьте права бота в канале.",
            parse_mode="HTML"
        )


# ========================================
# ОБРАБОТЧИКИ МЕНЮ
# ========================================

@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message, db):
    """Показ статистики"""
    if not is_admin(message.from_user.id):
        return

    try:
        channels = await db.get_channels()
        sources = await db.get_news_sources()

        text = f"""
📊 <b>Статистика</b>

🟢 <b>Бот:</b> Работает
📺 <b>Каналов:</b> {len(channels)}
📰 <b>Источников:</b> {len(sources)}

<b>Команды:</b>
/add_channel - добавить канал
/list_channels - список каналов
/test_post [ID] - тест
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.text == "📺 Мои каналы")
async def show_channels_menu(message: Message, db):
    """Меню каналов"""
    if not is_admin(message.from_user.id):
        return

    try:
        channels = await db.get_channels()

        if not channels:
            text = """
📺 <b>Каналы не настроены</b>

Добавьте первый канал:
1. Добавьте бота в канал как администратора
2. Используйте /add_channel
3. Введите ID канала
            """
        else:
            text = f"📺 <b>Каналов: {len(channels)}</b>\n\nИспользуйте /list_channels"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.text == "📰 Источники новостей")
async def show_sources_menu(message: Message, db):
    """Меню источников"""
    if not is_admin(message.from_user.id):
        return

    try:
        sources = await db.get_news_sources()
        active_sources = len([s for s in sources if s['is_active']])

        text = f"""
📰 <b>Источники новостей</b>

📊 <b>Статус:</b>
• Всего: {len(sources)}
• Активных: {active_sources}

<b>Основные источники:</b>
• Lenta.ru
• РИА Новости
• ТАСС
• Российская газета
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.text == "⚙️ Настройки")
async def show_settings_menu(message: Message, db):
    """Меню настроек"""
    if not is_admin(message.from_user.id):
        return

    try:
        model = await db.get_setting('openai_model') or 'gpt-4'
        style = await db.get_setting('default_style') or 'engaging'

        text = f"""
⚙️ <b>Настройки</b>

🤖 <b>ИИ:</b>
• Модель: {model}
• Стиль: {style}

📊 <b>Общие:</b>
• Интервал: 3 часа
• Постов в день: 5

<b>Команды настройки:</b>
/status - статус системы
/health_check - диагностика
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.text == "🚀 Запустить публикацию")
async def start_publication(message: Message, content_manager):
    """Запуск публикации"""
    if not is_admin(message.from_user.id):
        return

    try:
        await message.answer("🔄 Запуск обработки новостей...")

        if content_manager:
            await content_manager.process_and_publish_news()
            await message.answer("✅ Обработка завершена!")
        else:
            await message.answer("❌ Content Manager недоступен")

    except Exception as e:
        logger.error(f"Ошибка публикации: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.text == "⏹ Остановить бота")
async def stop_bot(message: Message):
    """Остановка бота"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⏹ <b>Остановка бота</b>\n\n"
        "Для остановки используйте Ctrl+C в терминале.\n"
        "Бот корректно сохранит состояние.",
        parse_mode="HTML"
    )


@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    """Справка"""
    if not is_admin(message.from_user.id):
        return

    help_text = """
ℹ️ <b>Справка по боту</b>

🤖 <b>Content Manager Bot v3.0.1</b>

📋 <b>Основные команды:</b>
• /start - главное меню
• /add_channel - добавить канал
• /list_channels - список каналов
• /test_post [ID] - тестовый пост
• /status - статус системы
• /health_check - диагностика

🎯 <b>Быстрый старт:</b>
1. Добавьте бота в канал как администратора
2. Используйте /add_channel
3. Введите ID канала
4. Запустите публикацию

🆘 <b>При проблемах:</b>
• Проверьте права бота в канале
• Используйте /health_check
• Проверьте логи в bot.log
    """

    await message.answer(help_text, parse_mode="HTML")


# ========================================
# ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ
# ========================================

@router.message()
async def handle_all_messages(message: Message, state: FSMContext):
    """Обработчик всех остальных сообщений"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return

    current_state = await state.get_state()
    if current_state:
        return  # Пропускаем если в состоянии FSM

    await message.answer(
        f"📨 Получено: {message.text}\n\n"
        f"Используйте /start для меню или команды:\n"
        f"/add_channel, /list_channels, /status",
        reply_markup=main_menu_keyboard()
    )


# ========================================
# ОБРАБОТЧИК CALLBACK ЗАПРОСОВ
# ========================================

@router.callback_query()
async def handle_callbacks(callback: CallbackQuery):
    """Обработчик callback запросов"""
    await callback.answer("🔧 Функция в разработке")


# ========================================
# ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ ДЛЯ ДИАГНОСТИКИ
# ========================================

@router.message(Command("debug"))
async def debug_command(message: Message, db, scheduler, monitor):
    """Отладочная информация"""
    if not is_admin(message.from_user.id):
        return

    debug_info = f"""
🔧 <b>ОТЛАДОЧНАЯ ИНФОРМАЦИЯ</b>

📊 <b>Статус компонентов:</b>
• DB: {'✅' if db else '❌'}
• Scheduler: {'✅' if scheduler else '❌'} ({scheduler.running if scheduler else 'N/A'})
• Monitor: {'✅' if monitor else '❌'} ({monitor.running if monitor else 'N/A'})

🔑 <b>Конфигурация:</b>
• BOT_TOKEN: {'✅' if config.BOT_TOKEN else '❌'}
• OPENAI_API_KEY: {'✅' if config.OPENAI_API_KEY else '❌'}
• ADMIN_ID: {config.ADMIN_ID}

📁 <b>База данных:</b>
• Путь: {config.DATABASE_PATH if hasattr(config, 'DATABASE_PATH') else 'N/A'}

⚙️ <b>Версия:</b> 3.0.1-fixed
    """

    await message.answer(debug_info, parse_mode="HTML")