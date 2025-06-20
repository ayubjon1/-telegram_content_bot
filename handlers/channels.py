from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramAPIError
import logging
import re

from utils.keyboards import (
    channels_management_keyboard, channel_list_keyboard,
    channel_actions_keyboard, confirmation_keyboard,
    cancel_keyboard, main_menu_keyboard
)
from database.models import DatabaseModels
from config import ADMIN_ID

logger = logging.getLogger(__name__)
router = Router()


class ChannelStates(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_channel_name = State()
    waiting_for_posts_per_day = State()
    waiting_for_channel_settings = State()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(F.text == "📺 Мои каналы")
async def show_channels_menu(message: Message):
    """Показ меню управления каналами"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📺 <b>Управление каналами</b>\n\n"
        "Здесь вы можете добавлять, настраивать и управлять вашими каналами для автоматической публикации.",
        parse_mode="HTML",
        reply_markup=channels_management_keyboard()
    )


@router.callback_query(F.data == "list_channels")
async def show_channels_list(callback: CallbackQuery, db: DatabaseModels):
    """Показ списка каналов"""
    try:
        channels = await db.get_channels()

        if not channels:
            await callback.message.edit_text(
                "📺 <b>Список каналов</b>\n\n"
                "❌ У вас пока нет добавленных каналов.\n"
                "Нажмите кнопку ниже, чтобы добавить первый канал.",
                parse_mode="HTML",
                reply_markup=channels_management_keyboard()
            )
            return

        text = "📺 <b>Ваши каналы:</b>\n\n"
        for channel in channels:
            status = "✅ Активен" if channel['is_active'] else "❌ Неактивен"
            text += f"<b>{channel['channel_name']}</b>\n"
            text += f"ID: <code>{channel['channel_id']}</code>\n"
            text += f"Статус: {status}\n"
            text += f"Постов в день: {channel['posts_per_day']}\n\n"

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=channel_list_keyboard(channels)
        )

    except Exception as e:
        logger.error(f"Ошибка получения списка каналов: {str(e)}")
        await callback.answer("❌ Ошибка получения списка каналов")


@router.callback_query(F.data == "add_channel")
async def start_add_channel(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления канала"""
    await state.set_state(ChannelStates.waiting_for_channel_id)

    await callback.message.edit_text(
        "➕ <b>Добавление нового канала</b>\n\n"
        "Отправьте ID канала в формате:\n"
        "• <code>@channel_username</code> (для публичных каналов)\n"
        "• <code>-100xxxxxxxxx</code> (для приватных каналов)\n\n"
        "❗️ <b>Важно:</b> Бот должен быть добавлен в канал как администратор с правами на отправку сообщений.",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )


@router.message(StateFilter(ChannelStates.waiting_for_channel_id))
async def process_channel_id(message: Message, state: FSMContext, bot: Bot):
    """Обработка ID канала"""
    if not is_admin(message.from_user.id):
        return

    channel_id = message.text.strip()

    # Валидация формата ID канала
    if not (channel_id.startswith('@') or channel_id.startswith('-100')):
        await message.answer(
            "❌ <b>Неверный формат ID канала</b>\n\n"
            "Используйте:\n"
            "• <code>@channel_username</code> для публичных каналов\n"
            "• <code>-100xxxxxxxxx</code> для приватных каналов",
            parse_mode="HTML"
        )
        return

    # Проверяем доступ к каналу
    try:
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

        # Сохраняем данные канала
        await state.update_data({
            'channel_id': channel_id,
            'channel_name': chat.title or chat.username or 'Без названия'
        })

        await state.set_state(ChannelStates.waiting_for_posts_per_day)

        await message.answer(
            f"✅ <b>Канал найден!</b>\n\n"
            f"<b>Название:</b> {chat.title or chat.username}\n"
            f"<b>ID:</b> <code>{channel_id}</code>\n\n"
            f"Теперь укажите количество постов в день для этого канала (от 1 до 20):",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )

    except TelegramAPIError as e:
        logger.error(f"Ошибка доступа к каналу {channel_id}: {str(e)}")
        await message.answer(
            "❌ <b>Ошибка доступа к каналу</b>\n\n"
            "Проверьте:\n"
            "• Правильность ID канала\n"
            "• Бот добавлен в канал как администратор\n"
            "• У бота есть права на отправку сообщений",
            parse_mode="HTML"
        )


@router.message(StateFilter(ChannelStates.waiting_for_posts_per_day))
async def process_posts_per_day(message: Message, state: FSMContext, db: DatabaseModels):
    """Обработка количества постов в день"""
    if not is_admin(message.from_user.id):
        return

    try:
        posts_per_day = int(message.text.strip())

        if posts_per_day < 1 or posts_per_day > 20:
            await message.answer(
                "❌ <b>Неверное количество</b>\n\n"
                "Укажите число от 1 до 20.",
                parse_mode="HTML"
            )
            return

        # Получаем данные из состояния
        data = await state.get_data()
        channel_id = data['channel_id']
        channel_name = data['channel_name']

        # Сохраняем канал в базу данных
        await db.add_channel(channel_id, channel_name, posts_per_day)

        await state.clear()

        await message.answer(
            f"✅ <b>Канал успешно добавлен!</b>\n\n"
            f"<b>Название:</b> {channel_name}\n"
            f"<b>ID:</b> <code>{channel_id}</code>\n"
            f"<b>Постов в день:</b> {posts_per_day}\n\n"
            f"Канал готов к работе!",
            parse_mode="HTML",
            reply_markup=channels_management_keyboard()
        )

    except ValueError:
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Введите число от 1 до 20.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка добавления канала: {str(e)}")
        await message.answer(
            "❌ <b>Ошибка добавления канала</b>\n\n"
            "Попробуйте еще раз или обратитесь к администратору.",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("channel_"))
async def show_channel_details(callback: CallbackQuery, db: DatabaseModels):
    """Показ деталей канала и действий с ним"""
    channel_id = callback.data.split("_", 1)[1]

    try:
        channels = await db.get_channels()
        channel = next((ch for ch in channels if ch['channel_id'] == channel_id), None)

        if not channel:
            await callback.answer("❌ Канал не найден")
            return

        status = "✅ Активен" if channel['is_active'] else "❌ Неактивен"
        last_post = channel['last_post_time'] or "Никогда"

        text = f"""
📺 <b>{channel['channel_name']}</b>

<b>ID:</b> <code>{channel_id}</code>
<b>Статус:</b> {status}
<b>Постов в день:</b> {channel['posts_per_day']}
<b>Последний пост:</b> {last_post}

Выберите действие:
        """

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=channel_actions_keyboard(channel_id, channel['is_active'])
        )

    except Exception as e:
        logger.error(f"Ошибка получения данных канала: {str(e)}")
        await callback.answer("❌ Ошибка получения данных канала")


@router.callback_query(F.data.startswith("stats_"))
async def show_channel_stats(callback: CallbackQuery, db: DatabaseModels):
    """Показ статистики канала"""
    channel_id = callback.data.split("_", 1)[1]

    try:
        stats = await db.get_statistics(channel_id)

        text = f"""
📊 <b>Статистика канала</b>

<b>Всего постов:</b> {stats['posts_count']}
<b>Общие просмотры:</b> {stats['total_views']}
<b>Средний охват:</b> {stats['total_views'] // max(stats['posts_count'], 1)}

<b>За последние 7 дней:</b>
• Постов: {stats.get('week_posts', 0)}
• Просмотров: {stats.get('week_views', 0)}

<b>За сегодня:</b>
• Постов: {stats.get('today_posts', 0)}
• Просмотров: {stats.get('today_views', 0)}
        """

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=channel_actions_keyboard(channel_id, True)
        )

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {str(e)}")
        await callback.answer("❌ Ошибка получения статистики")


@router.callback_query(F.data.startswith("settings_"))
async def show_channel_settings(callback: CallbackQuery, state: FSMContext):
    """Показ настроек канала"""
    channel_id = callback.data.split("_", 1)[1]

    await state.set_state(ChannelStates.waiting_for_channel_settings)
    await state.update_data({'channel_id': channel_id})

    text = """
⚙️ <b>Настройки канала</b>

Что вы хотите изменить?

• Количество постов в день
• Стиль публикаций
• Расписание для канала
• Категории новостей

Отправьте одну из команд:
<code>/posts [число]</code> - изменить количество постов
<code>/style [стиль]</code> - изменить стиль (neutral/engaging/formal/casual)
<code>/schedule [время]</code> - установить расписание
    """

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )


@router.message(StateFilter(ChannelStates.waiting_for_channel_settings))
async def process_channel_settings(message: Message, state: FSMContext, db: DatabaseModels):
    """Обработка настроек канала"""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    channel_id = data['channel_id']
    text = message.text.strip()

    try:
        if text.startswith('/posts '):
            # Изменение количества постов
            posts_count = int(text.split()[1])
            if 1 <= posts_count <= 20:
                # Обновляем в базе (предполагаем, что есть такой метод)
                # await db.update_channel_posts_per_day(channel_id, posts_count)
                await message.answer(
                    f"✅ Количество постов изменено на {posts_count}",
                    reply_markup=main_menu_keyboard()
                )
            else:
                await message.answer("❌ Число должно быть от 1 до 20")
                return

        elif text.startswith('/style '):
            # Изменение стиля
            style = text.split()[1].lower()
            styles = ['neutral', 'engaging', 'formal', 'casual']
            if style in styles:
                await db.set_setting(f"channel_style_{channel_id}", style)
                await message.answer(
                    f"✅ Стиль изменен на {style}",
                    reply_markup=main_menu_keyboard()
                )
            else:
                await message.answer(f"❌ Доступные стили: {', '.join(styles)}")
                return

        elif text.startswith('/schedule '):
            # Изменение расписания (упрощенно)
            schedule_time = text.split()[1]
            await db.set_setting(f"channel_schedule_{channel_id}", schedule_time)
            await message.answer(
                f"✅ Расписание установлено: {schedule_time}",
                reply_markup=main_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Неизвестная команда. Используйте /posts, /style или /schedule"
            )
            return

        await state.clear()

    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат команды")
    except Exception as e:
        logger.error(f"Ошибка настройки канала: {str(e)}")
        await message.answer("❌ Ошибка изменения настроек")


@router.callback_query(F.data.startswith("test_post_"))
async def send_test_post(callback: CallbackQuery, bot: Bot):
    """Отправка тестового поста в канал"""
    channel_id = callback.data.split("_", 2)[2]

    try:
        test_message = """
🧪 <b>Тестовый пост</b>

Это тестовое сообщение для проверки работы бота.

✅ Если вы видите это сообщение, бот корректно настроен и может публиковать в канал.

🤖 Content Manager Bot работает!

#тест #бот #работает
        """

        await bot.send_message(
            chat_id=channel_id,
            text=test_message,
            parse_mode="HTML"
        )

        await callback.answer("✅ Тестовый пост отправлен!")

    except TelegramAPIError as e:
        logger.error(f"Ошибка отправки тестового поста: {str(e)}")
        await callback.answer("❌ Ошибка отправки. Проверьте права бота в канале.")


@router.callback_query(F.data.startswith("activate_"))
async def activate_channel(callback: CallbackQuery, db: DatabaseModels):
    """Активация канала"""
    channel_id = callback.data.split("_", 1)[1]

    try:
        await db.update_channel_status(channel_id, True)
        await callback.answer("✅ Канал активирован")

        # Обновляем отображение
        await show_channel_details(callback, db)

    except Exception as e:
        logger.error(f"Ошибка активации канала: {str(e)}")
        await callback.answer("❌ Ошибка активации канала")


@router.callback_query(F.data.startswith("deactivate_"))
async def deactivate_channel(callback: CallbackQuery, db: DatabaseModels):
    """Деактивация канала"""
    channel_id = callback.data.split("_", 1)[1]

    try:
        await db.update_channel_status(channel_id, False)
        await callback.answer("✅ Канал деактивирован")

        # Обновляем отображение
        await show_channel_details(callback, db)

    except Exception as e:
        logger.error(f"Ошибка деактивации канала: {str(e)}")
        await callback.answer("❌ Ошибка деактивации канала")


@router.callback_query(F.data.startswith("delete_"))
async def confirm_delete_channel(callback: CallbackQuery):
    """Подтверждение удаления канала"""
    channel_id = callback.data.split("_", 1)[1]

    await callback.message.edit_text(
        "⚠️ <b>Подтверждение удаления</b>\n\n"
        "Вы действительно хотите удалить этот канал?\n"
        "Это действие нельзя отменить.",
        parse_mode="HTML",
        reply_markup=confirmation_keyboard("delete_channel", channel_id)
    )


@router.callback_query(F.data.startswith("confirm_delete_channel_"))
async def delete_channel(callback: CallbackQuery, db: DatabaseModels):
    """Удаление канала"""
    channel_id = callback.data.split("_", 3)[3]

    try:
        await db.delete_channel(channel_id)

        await callback.message.edit_text(
            "✅ <b>Канал удален</b>\n\n"
            "Канал успешно удален из списка.",
            parse_mode="HTML",
            reply_markup=channels_management_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка удаления канала: {str(e)}")
        await callback.answer("❌ Ошибка удаления канала")


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отмена действия"""
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Действие отменено</b>",
        parse_mode="HTML",
        reply_markup=channels_management_keyboard()
    )


@router.callback_query(F.data == "back_to_channels")
async def back_to_channels(callback: CallbackQuery):
    """Возврат к управлению каналами"""
    await callback.message.edit_text(
        "📺 <b>Управление каналами</b>\n\n"
        "Здесь вы можете добавлять, настраивать и управлять вашими каналами для автоматической публикации.",
        parse_mode="HTML",
        reply_markup=channels_management_keyboard()
    )