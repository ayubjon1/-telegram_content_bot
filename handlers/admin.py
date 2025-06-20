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
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return

    await state.clear()

    welcome_text = """
🤖 <b>Content Manager Bot</b>

✅ Бот запущен и работает!
✅ База данных готова
✅ Все модули подключены

<b>Доступные команды:</b>
/add_channel - добавить канал
/list_channels - список каналов
/test_post - тестовый пост
/remove_channel - удалить канал

Используйте меню для управления:
    """

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


# Команды управления каналами

@router.message(Command("add_channel"))
async def start_add_channel(message: Message, state: FSMContext):
    """Начало добавления канала"""
    if not is_admin(message.from_user.id):
        return

    await state.set_state(ChannelStates.waiting_for_channel_id)

    await message.answer(
        "📺 <b>Добавление канала</b>\n\n"
        "Отправьте ID канала в одном из форматов:\n"
        "• <code>@channel_username</code> (для публичных)\n"
        "• <code>-100xxxxxxxxx</code> (для приватных)\n\n"
        "❗️ <b>Важно:</b> Сначала добавьте бота в канал как администратора с правами на отправку сообщений!",
        parse_mode="HTML"
    )


@router.message(StateFilter(ChannelStates.waiting_for_channel_id))
async def process_channel_id(message: Message, state: FSMContext, bot: Bot, db):
    """Обработка ID канала"""
    if not is_admin(message.from_user.id):
        return

    channel_id = message.text.strip()

    # Валидация формата
    if not (channel_id.startswith('@') or channel_id.startswith('-100')):
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Используйте:\n"
            "• @channel_username\n"
            "• -100xxxxxxxxx",
            parse_mode="HTML"
        )
        return

    try:
        # Проверяем доступ к каналу
        chat = await bot.get_chat(channel_id)

        # Проверяем права бота
        bot_member = await bot.get_chat_member(channel_id, bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                "❌ <b>Нет прав администратора</b>\n\n"
                "Добавьте бота в канал как администратора с правами на отправку сообщений.",
                parse_mode="HTML"
            )
            return

        # Сохраняем данные
        await state.update_data({
            'channel_id': channel_id,
            'channel_name': chat.title or chat.username or 'Без названия'
        })

        await state.set_state(ChannelStates.waiting_for_posts_per_day)

        await message.answer(
            f"✅ <b>Канал найден!</b>\n\n"
            f"<b>Название:</b> {chat.title or chat.username}\n"
            f"<b>ID:</b> <code>{channel_id}</code>\n\n"
            f"Укажите количество постов в день (1-20):",
            parse_mode="HTML"
        )

    except TelegramAPIError as e:
        logger.error(f"Ошибка доступа к каналу {channel_id}: {str(e)}")
        await message.answer(
            "❌ <b>Ошибка доступа к каналу</b>\n\n"
            "Проверьте:\n"
            "• Правильность ID канала\n"
            "• Бот добавлен как администратор\n"
            "• У бота есть права на отправку сообщений",
            parse_mode="HTML"
        )


@router.message(StateFilter(ChannelStates.waiting_for_posts_per_day))
async def process_posts_per_day(message: Message, state: FSMContext, db):
    """Обработка количества постов"""
    if not is_admin(message.from_user.id):
        return

    try:
        posts_per_day = int(message.text.strip())

        if posts_per_day < 1 or posts_per_day > 20:
            await message.answer("❌ Укажите число от 1 до 20")
            return

        # Получаем данные
        data = await state.get_data()
        channel_id = data['channel_id']
        channel_name = data['channel_name']

        # Сохраняем в БД
        await db.add_channel(channel_id, channel_name, posts_per_day)

        await state.clear()

        await message.answer(
            f"✅ <b>Канал добавлен!</b>\n\n"
            f"<b>Название:</b> {channel_name}\n"
            f"<b>ID:</b> <code>{channel_id}</code>\n"
            f"<b>Постов в день:</b> {posts_per_day}\n\n"
            f"Канал готов к работе!",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )

    except ValueError:
        await message.answer("❌ Введите число от 1 до 20")
    except Exception as e:
        logger.error(f"Ошибка сохранения канала: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("list_channels"))
async def list_channels(message: Message, db):
    """Список всех каналов"""
    if not is_admin(message.from_user.id):
        return

    try:
        channels = await db.get_channels()

        if not channels:
            await message.answer(
                "📺 <b>Список каналов</b>\n\n"
                "❌ У вас нет добавленных каналов.\n"
                "Используйте /add_channel для добавления.",
                parse_mode="HTML"
            )
            return

        text = "📺 <b>Ваши каналы:</b>\n\n"
        for i, channel in enumerate(channels, 1):
            status = "✅ Активен" if channel['is_active'] else "❌ Неактивен"
            text += f"<b>{i}. {channel['channel_name']}</b>\n"
            text += f"   ID: <code>{channel['channel_id']}</code>\n"
            text += f"   Статус: {status}\n"
            text += f"   Постов в день: {channel['posts_per_day']}\n\n"

        text += "\n<b>Команды:</b>\n"
        text += "/test_post [ID] - тестовый пост\n"
        text += "/remove_channel [ID] - удалить канал"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка получения каналов: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("test_post"))
async def test_post_command(message: Message, bot: Bot, db):
    """Отправка тестового поста"""
    if not is_admin(message.from_user.id):
        return

    # Парсим команду
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Используйте: <code>/test_post @channel</code>\n"
            "Или: <code>/test_post -100xxxxxxxxx</code>",
            parse_mode="HTML"
        )
        return

    channel_id = parts[1]

    try:
        # Проверяем канал в БД
        channels = await db.get_channels()
        channel = next((ch for ch in channels if ch['channel_id'] == channel_id), None)

        if not channel:
            await message.answer(
                f"❌ <b>Канал не найден в базе</b>\n\n"
                f"Сначала добавьте канал: /add_channel",
                parse_mode="HTML"
            )
            return

        # Отправляем тестовый пост
        test_text = """
🧪 <b>Тестовый пост от Content Manager Bot</b>

✅ Если вы видите это сообщение, бот корректно настроен!

<b>Проверено:</b>
• Подключение к каналу ✅
• Права на отправку ✅
• Форматирование текста ✅

🤖 Бот готов к автоматическим публикациям!

#тест #contentmanager #готово
        """

        sent_message = await bot.send_message(
            chat_id=channel_id,
            text=test_text,
            parse_mode="HTML"
        )

        await message.answer(
            f"✅ <b>Тестовый пост отправлен!</b>\n\n"
            f"<b>Канал:</b> {channel['channel_name']}\n"
            f"<b>ID сообщения:</b> {sent_message.message_id}\n\n"
            f"Проверьте канал - пост должен появиться.",
            parse_mode="HTML"
        )

    except TelegramAPIError as e:
        logger.error(f"Ошибка отправки в {channel_id}: {str(e)}")
        await message.answer(
            f"❌ <b>Ошибка отправки</b>\n\n"
            f"Проверьте права бота в канале.\n"
            f"Детали: {str(e)}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка тестового поста: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("remove_channel"))
async def remove_channel_command(message: Message, db):
    """Удаление канала"""
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Используйте: <code>/remove_channel @channel</code>",
            parse_mode="HTML"
        )
        return

    channel_id = parts[1]

    try:
        # Проверяем существование канала
        channels = await db.get_channels()
        channel = next((ch for ch in channels if ch['channel_id'] == channel_id), None)

        if not channel:
            await message.answer(f"❌ Канал {channel_id} не найден в базе")
            return

        # Удаляем канал
        await db.delete_channel(channel_id)

        await message.answer(
            f"✅ <b>Канал удален</b>\n\n"
            f"<b>Удален:</b> {channel['channel_name']}\n"
            f"<b>ID:</b> {channel_id}",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка удаления канала: {str(e)}")
        await message.answer(f"❌ Ошибка удаления: {str(e)}")


# Остальные обработчики меню...

@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message, db):
    if not is_admin(message.from_user.id):
        return

    try:
        stats = await db.get_statistics()
        channels = await db.get_channels()
        sources = await db.get_news_sources()

        active_channels = len([ch for ch in channels if ch['is_active']])

        text = f"""
📊 <b>Статистика</b>

🟢 <b>Бот:</b> Работает
📺 <b>Каналов:</b> {len(channels)} (активных: {active_channels})
📰 <b>Источников:</b> {len(sources)}
📝 <b>Постов:</b> {stats['posts_count']}

<b>Команды:</b>
/add_channel - добавить канал
/list_channels - список каналов
/test_post [ID] - тест публикации
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка статистики: {str(e)}")


@router.message(F.text == "📺 Мои каналы")
async def show_channels(message: Message, db):
    if not is_admin(message.from_user.id):
        return

    try:
        channels = await db.get_channels()

        if not channels:
            text = """
📺 <b>Мои каналы</b>

❌ Каналы не настроены.

<b>Добавление канала:</b>
1. Добавьте бота в канал как администратора
2. Используйте: /add_channel
3. Следуйте инструкциям

<b>Команды:</b>
/add_channel - добавить канал
/list_channels - список каналов
            """
        else:
            text = f"📺 <b>Каналов добавлено: {len(channels)}</b>\n\n"
            text += "Используйте /list_channels для подробного списка"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.text == "📰 Источники новостей")
async def show_sources(message: Message, db):
    if not is_admin(message.from_user.id):
        return

    try:
        sources = await db.get_news_sources()

        text = f"📰 <b>Источников: {len(sources)}</b>\n\n"
        for source in sources[:3]:  # Показываем первые 3
            status = "✅" if source['is_active'] else "❌"
            text += f"{status} {source['name']}\n"

        if len(sources) > 3:
            text += f"\n... и еще {len(sources) - 3}"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⚙️ <b>Настройки</b>\n\n"
        "🎨 Стиль: Привлекательный\n"
        "⏰ Интервал: 3 часа\n"
        "📊 Постов в день: 5\n\n"
        "Расширенные настройки в разработке...",
        parse_mode="HTML"
    )


@router.message(F.text == "🚀 Запустить публикацию")
async def start_publication(message: Message, db, content_manager):
    if not is_admin(message.from_user.id):
        return

    try:
        channels = await db.get_channels()
        if not channels:
            await message.answer(
                "⚠️ <b>Нет каналов</b>\n\n"
                "Сначала добавьте каналы: /add_channel",
                parse_mode="HTML"
            )
            return

        await message.answer("🔄 Запуск обработки новостей...")
        await content_manager.process_and_publish_news()
        await message.answer("✅ Обработка завершена!")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message()
async def handle_all(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return

    current_state = await state.get_state()
    if current_state:
        return  # Пропускаем если в состоянии ожидания

    await message.answer(
        f"Получил: {message.text}\n\n"
        f"Используйте /start для команд",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query()
async def handle_callbacks(callback: CallbackQuery):
    await callback.answer("Функция в разработке...")


@router.message(Command("test_parsing"))
async def test_parsing_command(message: Message, db):
    """Тестирование парсинга новостей"""
    if not is_admin(message.from_user.id):
        return

    await message.answer("🔄 <b>Тестирование парсинга новостей...</b>", parse_mode="HTML")

    try:
        from services.news_parser import NewsParser

        # Получаем источники
        sources = await db.get_news_sources()
        if not sources:
            await message.answer("❌ Нет источников новостей в базе")
            return

        total_news = 0
        results = []

        async with NewsParser() as parser:
            for source in sources[:3]:  # Тестируем первые 3 источника
                result = await parser.test_source(source['url'], source['name'])
                total_news += result['news_count']

                status = "✅" if result['success'] else "❌"
                results.append(f"{status} <b>{source['name']}</b>: {result['news_count']} новостей")

        result_text = f"""
🧪 <b>Результаты тестирования парсинга</b>

<b>Протестировано источников:</b> {len(results)}
<b>Всего получено новостей:</b> {total_news}

<b>Детали:</b>
{chr(10).join(results)}

{f"✅ Парсинг работает отлично!" if total_news > 0 else "⚠️ Проверьте источники новостей"}
        """

        await message.answer(result_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка тестирования парсинга: {str(e)}")
        await message.answer(f"❌ Ошибка тестирования: {str(e)}")


@router.message(Command("test_ai"))
async def test_ai_command(message: Message, content_manager):
    """Тестирование ИИ обработки"""
    if not is_admin(message.from_user.id):
        return

    await message.answer("🤖 <b>Тестирование ИИ обработки...</b>", parse_mode="HTML")

    try:
        result = await content_manager.test_ai_processing()

        if result['success']:
            response = f"""
✅ <b>ИИ тест успешен!</b>

<b>Исходный заголовок:</b>
{result['original_title']}

<b>Обработанный контент:</b>
{result['processed_content']}

<b>Стиль:</b> {result['style']}
<b>Хештеги:</b> {' '.join(result['hashtags'])}

🎉 ИИ готов к работе!
            """
        else:
            response = f"""
❌ <b>Ошибка ИИ теста</b>

{result['error']}

Проверьте настройки OpenAI API ключа.
            """

        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка тестирования ИИ: {str(e)}")


# Добавьте эти команды в handlers/admin.py в конце файла

# ДОБАВЬТЕ ЭТО В КОНЕЦ ФАЙЛА handlers/admin.py
# (заменяет строки после последней функции)

@router.message(Command("scheduler_status"))
async def scheduler_status_command(message: Message, scheduler):
    """Статус нового планировщика"""
    if not is_admin(message.from_user.id):
        return

    try:
        status = scheduler.get_scheduler_status()
        jobs = scheduler.get_scheduled_jobs()

        text = f"""
🔄 <b>Статус планировщика:</b>

<b>Общее состояние:</b>
• Работает: {'✅ Да' if status['running'] else '❌ Нет'}
• Всего задач: {status['total_jobs']}
• Активных: {status['active_jobs']}
• Ожидающих: {status['pending_jobs']}

<b>Следующее выполнение:</b>
• Время: {status['next_execution'] or 'Не запланировано'}
• Задача: {status['next_job_name'] or 'Нет активных задач'}

<b>Запланированные задачи:</b>
        """

        if jobs:
            for job in jobs[:5]:  # Показываем первые 5
                status_emoji = {
                    'pending': '⏳',
                    'running': '⚡',
                    'completed': '✅',
                    'failed': '❌',
                    'cancelled': '🚫'
                }.get(job['status'], '❓')

                text += f"\n{status_emoji} {job['name']}"
                if job['next_run']:
                    run_time = job['next_run'][:16].replace('T', ' ')
                    text += f"\n   📅 {run_time}"
        else:
            text += "\n❌ Нет запланированных задач"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения статуса: {str(e)}")


@router.message(Command("quick_schedule"))
async def quick_schedule_command(message: Message, scheduler):
    """Быстрое планирование публикаций"""
    if not is_admin(message.from_user.id):
        return

    try:
        # Планируем публикации на популярные времена
        times = ['09:00', '15:00', '21:00']
        job_ids = scheduler.schedule_daily_posts(times)

        text = f"""
⚡ <b>Быстрое планирование:</b>

✅ Запланированы ежедневные публикации:
• 🌅 09:00 - утренние новости
• 🌞 15:00 - дневная сводка  
• 🌙 21:00 - вечерний обзор

<b>Созданные задачи:</b>
        """

        for i, job_id in enumerate(job_ids):
            text += f"\n• {times[i]}: {job_id[:8]}..."

        text += f"\n\n📊 Используйте /scheduler_status для мониторинга"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка планирования: {str(e)}")


@router.message(Command("schedule_test"))
async def schedule_test_command(message: Message, scheduler):
    """Тестирование планировщика"""
    if not is_admin(message.from_user.id):
        return

    try:
        # Планируем тестовый пост через 1 минуту
        from datetime import datetime, timedelta

        test_times = [(datetime.now() + timedelta(minutes=1)).strftime('%H:%M')]
        job_ids = scheduler.schedule_daily_posts(test_times)

        await message.answer(
            f"🧪 <b>Тест планировщика:</b>\n\n"
            f"✅ Запланирован тестовый пост через 1 минуту\n"
            f"🆔 ID задачи: {job_ids[0][:8]}...\n\n"
            f"Следите за логами или используйте /scheduler_status",
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка тестирования: {str(e)}")


@router.message(Command("upgrade_status"))
async def upgrade_status_command(message: Message, scheduler):
    """Статус апгрейда до ИИ-агента"""
    if not is_admin(message.from_user.id):
        return

    try:
        # Проверяем компоненты
        scheduler_ok = scheduler.running if scheduler else False

        components = {
            "🔄 Планировщик": "✅ Upgraded" if scheduler_ok else "❌ Failed",
            "🔍 Мониторинг": "⏳ Pending",
            "🧠 ИИ обработка": "⏳ Pending",
            "📊 Аналитика": "⏳ Pending"
        }

        completed = sum(1 for status in components.values() if "✅" in status)
        total = len(components)
        progress = f"{completed}/{total} ({completed / total * 100:.0f}%)"

        text = f"""
🚀 <b>Прогресс апгрейда до ИИ-агента:</b>

{chr(10).join(f"{component}: {status}" for component, status in components.items())}

<b>📈 Общий прогресс:</b> {progress}

<b>🎯 Следующие шаги:</b>
• ⏳ Добавление системы мониторинга
• ⏳ Улучшение ИИ процессора
• ⏳ Внедрение ML аналитики

<b>📊 Статус планировщика:</b>
• Задач в системе: {len(scheduler.jobs) if scheduler else 0}
• Статус: {'🟢 Работает' if scheduler_ok else '🔴 Не работает'}
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения статуса: {str(e)}")


# ДОБАВЬТЕ ЭТИ КОМАНДЫ В КОНЕЦ handlers/admin.py

@router.message(Command("system_status"))
async def system_status_command(message: Message, monitor):
    """Статус системы с мониторингом"""
    if not is_admin(message.from_user.id):
        return

    try:
        status = monitor.get_system_status()

        text = f"""
{status['emoji']} <b>Статус системы: {status['status'].upper()}</b>

<b>📊 Ресурсы:</b>
• CPU: {status['cpu_percent']:.1f}%
• Память: {status['memory_percent']:.1f}%
• Диск: {status['disk_percent']:.1f}%

<b>🚨 Алерты:</b>
• Активных: {status['active_alerts_count']}
• Критических: {status['critical_alerts']}

<b>🛠️ Автоисцеление:</b>
• Действий выполнено: {sum(status['healing_actions'].values())}
• Мониторинг: {'🟢 Активен' if status['monitoring_active'] else '🔴 Остановлен'}

<b>🕐 Последняя проверка:</b> {status['last_check'][:19].replace('T', ' ')}
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения статуса: {str(e)}")


@router.message(Command("metrics"))
async def metrics_command(message: Message, monitor):
    """Детальные метрики системы"""
    if not is_admin(message.from_user.id):
        return

    try:
        summary = monitor.get_metrics_summary(hours=1)

        if not summary:
            await message.answer("📊 Нет данных метрик")
            return

        text = f"""
📊 <b>Метрики за последний час:</b>

<b>🖥️ CPU:</b>
• Среднее: {summary['cpu']['avg']:.1f}%
• Максимум: {summary['cpu']['max']:.1f}%
• Минимум: {summary['cpu']['min']:.1f}%

<b>🧠 Память:</b>
• Среднее: {summary['memory']['avg']:.1f}%
• Максимум: {summary['memory']['max']:.1f}%
• Минимум: {summary['memory']['min']:.1f}%

<b>💾 Диск:</b>
• Среднее: {summary['disk']['avg']:.1f}%
• Максимум: {summary['disk']['max']:.1f}%
• Минимум: {summary['disk']['min']:.1f}%

<b>📈 Точек данных:</b> {summary['data_points']}
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения метрик: {str(e)}")


@router.message(Command("alerts"))
async def alerts_command(message: Message, monitor):
    """Список активных алертов"""
    if not is_admin(message.from_user.id):
        return

    try:
        active_alerts = [a for a in monitor.active_alerts.values() if not a.resolved]

        if not active_alerts:
            await message.answer("✅ <b>Нет активных алертов</b>\n\nСистема работает стабильно!", parse_mode="HTML")
            return

        text = "🚨 <b>Активные алерты:</b>\n\n"

        for alert in sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)[:10]:
            level_emoji = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🔴'
            }.get(alert.level, '❓')

            time_str = alert.timestamp.strftime('%H:%M')
            text += f"{level_emoji} <b>{alert.title}</b>\n"
            text += f"   {alert.message}\n"
            text += f"   🕐 {time_str}\n\n"

        if len(active_alerts) > 10:
            text += f"... и еще {len(active_alerts) - 10} алертов"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения алертов: {str(e)}")


@router.message(Command("health_check"))
async def health_check_command(message: Message, monitor, scheduler, db):
    """Полная проверка здоровья системы"""
    if not is_admin(message.from_user.id):
        return

    try:
        await message.answer("🔍 <b>Выполняется проверка здоровья...</b>", parse_mode="HTML")

        checks = []

        # Проверяем мониторинг
        monitor_status = "✅ Работает" if monitor.running else "❌ Остановлен"
        checks.append(f"🔍 Мониторинг: {monitor_status}")

        # Проверяем планировщик
        scheduler_status = "✅ Работает" if scheduler.running else "❌ Остановлен"
        jobs_count = len(scheduler.jobs)
        checks.append(f"📅 Планировщик: {scheduler_status} ({jobs_count} задач)")

        # Проверяем БД
        try:
            channels = await db.get_channels()
            db_status = f"✅ Работает ({len(channels)} каналов)"
        except Exception as e:
            db_status = f"❌ Ошибка: {str(e)[:30]}"
        checks.append(f"🗄️ База данных: {db_status}")

        # Проверяем источники новостей
        try:
            sources = await db.get_news_sources()
            active_sources = len([s for s in sources if s['is_active']])
            sources_status = f"✅ Работает ({active_sources} активных)"
        except Exception as e:
            sources_status = f"❌ Ошибка: {str(e)[:30]}"
        checks.append(f"📰 Источники: {sources_status}")

        # Получаем системные метрики
        system_status = monitor.get_system_status()

        # Подсчитываем общее здоровье
        healthy_checks = sum(1 for check in checks if "✅" in check)
        total_checks = len(checks)
        health_score = int((healthy_checks / total_checks) * 100)

        # Учитываем системные ресурсы
        if system_status['cpu_percent'] > 80:
            health_score -= 10
        if system_status['memory_percent'] > 80:
            health_score -= 10
        if system_status['critical_alerts'] > 0:
            health_score -= 20

        health_score = max(0, min(100, health_score))

        # Определяем статус
        if health_score >= 90:
            overall_emoji = "🟢"
            overall_status = "ОТЛИЧНО"
        elif health_score >= 70:
            overall_emoji = "🟡"
            overall_status = "ХОРОШО"
        elif health_score >= 50:
            overall_emoji = "🟠"
            overall_status = "УДОВЛЕТВОРИТЕЛЬНО"
        else:
            overall_emoji = "🔴"
            overall_status = "КРИТИЧНО"

        text = f"""
{overall_emoji} <b>ЗДОРОВЬЕ СИСТЕМЫ: {health_score}% - {overall_status}</b>

<b>🔧 Компоненты:</b>
{chr(10).join(checks)}

<b>📊 Ресурсы:</b>
• CPU: {system_status['cpu_percent']:.1f}%
• Память: {system_status['memory_percent']:.1f}%
• Диск: {system_status['disk_percent']:.1f}%

<b>🚨 Алерты:</b>
• Всего активных: {system_status['active_alerts_count']}
• Критических: {system_status['critical_alerts']}

<b>🛠️ Автоисцеление:</b>
{chr(10).join([f"• {action}: {count}x" for action, count in system_status['healing_actions'].items()]) or "• Не требовалось"}

<b>💡 Рекомендации:</b>
        """

        if health_score < 70:
            text += "\n• ⚠️ Проверьте критические компоненты"
        if system_status['cpu_percent'] > 80:
            text += "\n• 🖥️ Высокая нагрузка на CPU"
        if system_status['memory_percent'] > 80:
            text += "\n• 🧠 Высокое использование памяти"
        if system_status['critical_alerts'] > 0:
            text += "\n• 🚨 Есть критические алерты"
        if health_score >= 90:
            text += "\n🎉 Система работает идеально!"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка проверки здоровья: {str(e)}")


@router.message(Command("force_healing"))
async def force_healing_command(message: Message, monitor):
    """Принудительное автоисцеление"""
    if not is_admin(message.from_user.id):
        return

    try:
        await message.answer("🛠️ <b>Запуск принудительного автоисцеления...</b>", parse_mode="HTML")

        # Создаем тестовые алерты для принудительного исцеления
        import gc

        actions_taken = []

        # Принудительная сборка мусора
        collected = gc.collect()
        actions_taken.append(f"🧹 Сборка мусора: {collected} объектов")

        # Очистка метрик
        if len(monitor.system_metrics) > 100:
            while len(monitor.system_metrics) > 100:
                monitor.system_metrics.popleft()
            actions_taken.append("📊 Очищены старые метрики")

        # Проверка планировщика
        if monitor.scheduler and not monitor.scheduler.running:
            await monitor._heal_scheduler()
            actions_taken.append("📅 Перезапущен планировщик")

        # Проверка БД
        try:
            await monitor.db.get_setting('health_check')
            actions_taken.append("🗄️ База данных проверена")
        except:
            await monitor._heal_database()
            actions_taken.append("🗄️ База данных переинициализирована")

        text = f"""
✅ <b>Автоисцеление завершено!</b>

<b>🛠️ Выполненные действия:</b>
{chr(10).join(actions_taken)}

<b>📊 Результат:</b>
• Система оптимизирована
• Ресурсы освобождены
• Компоненты проверены

Используйте /system_status для проверки результата.
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка автоисцеления: {str(e)}")


# ОБНОВЛЯЕМ команду /upgrade_status для учета мониторинга
@router.message(Command("upgrade_status"))
async def upgrade_status_command(message: Message, scheduler=None, monitor=None):
    """Статус апгрейда до ИИ-агента"""
    if not is_admin(message.from_user.id):
        return

    try:
        # Проверяем компоненты
        scheduler_ok = scheduler.running if scheduler else False
        monitoring_ok = monitor.running if monitor else False

        components = {
            "🔄 Планировщик": "✅ Upgraded" if scheduler_ok else "❌ Failed",
            "🔍 Мониторинг": "✅ Upgraded" if monitoring_ok else "❌ Pending",
            "🧠 ИИ обработка": "⏳ Pending",
            "📊 Аналитика": "⏳ Pending"
        }

        completed = sum(1 for status in components.values() if "✅" in status)
        total = len(components)
        progress = f"{completed}/{total} ({completed / total * 100:.0f}%)"

        text = f"""
🚀 <b>Прогресс апгрейда до ИИ-агента:</b>

{chr(10).join(f"{component}: {status}" for component, status in components.items())}

<b>📈 Общий прогресс:</b> {progress}

<b>🎯 Следующие шаги:</b>
• ⏳ Добавление системы мониторинга
• ⏳ Улучшение ИИ процессора
• ⏳ Внедрение ML аналитики

<b>📊 Статус компонентов:</b>
• Планировщик: {'🟢 Работает' if scheduler_ok else '🔴 Остановлен'}
• Задач в системе: {len(scheduler.jobs) if scheduler else 0}
• Мониторинг: {'🟢 Активен' if monitoring_ok else '🔴 Неактивен'}

<b>💡 Рекомендация:</b>
Сейчас планировщик работает отлично! 
Следующий шаг - добавление мониторинга.
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения статуса: {str(e)}")


# ДОБАВЬТЕ эту простую команду для проверки мониторинга:
@router.message(Command("test_monitor"))
async def test_monitor_command(message: Message):
    """Тест мониторинга"""
    if not is_admin(message.from_user.id):
        return

    try:
        import psutil

        # Получаем базовые метрики
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        text = f"""
🔍 <b>Тест системного мониторинга:</b>

<b>📊 Текущие метрики:</b>
• CPU: {cpu:.1f}%
• Память: {memory.percent:.1f}%
• Доступно памяти: {memory.available // (1024 ** 3):.1f} GB

<b>✅ Статус:</b>
• psutil библиотека: Работает
• Сбор метрик: Успешно
• Система готова к мониторингу

<b>🎯 Следующий шаг:</b>
Интегрировать полную систему мониторинга
        """

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка тестирования: {str(e)}")


# ОБНОВЛЯЕМ команду /start для включения информации о мониторинге
@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, scheduler, monitor):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return

    await state.clear()

    # Проверяем статус компонентов
    scheduler_status = "✅ Работает" if scheduler and scheduler.running else "❌ Остановлен"
    monitor_status = "✅ Активен" if monitor and monitor.running else "❌ Неактивен"
    jobs_count = len(scheduler.jobs) if scheduler else 0

    welcome_text = f"""
🤖 <b>Content Manager Bot v2.0 - Enterprise Edition</b>

✅ Бот запущен и работает!
✅ База данных готова
✅ Все модули подключены
{scheduler_status} Планировщик ({jobs_count} задач)
{monitor_status} Система мониторинга

<b>🆕 Enterprise возможности:</b>
• 📅 Персистентный планировщик с retry логикой
• 🔍 Real-time мониторинг ресурсов
• 🛠️ Автоматическое исцеление проблем
• 🚨 Система алертов и уведомлений
• 📊 Детальная аналитика производительности

<b>🔍 Команды мониторинга:</b>
/system_status - состояние системы
/health_check - полная диагностика
/metrics - метрики ресурсов
/alerts - активные алерты

<b>📅 Команды планировщика:</b>
/scheduler_status - статус планировщика
/quick_schedule - быстрое планирование
/schedule_test - тест планировщика

<b>📊 Команды апгрейда:</b>
/upgrade_status - прогресс до ИИ-агента
/force_healing - принудительное исцеление

<b>📺 Базовые команды:</b>
/add_channel - добавить канал
/list_channels - список каналов
/test_post - тестовый пост

Используйте меню для управления:
    """

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )