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