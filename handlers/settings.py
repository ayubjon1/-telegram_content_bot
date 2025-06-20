from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from utils.keyboards import (
    settings_keyboard, schedule_settings_keyboard, style_settings_keyboard,
    time_selection_keyboard, interval_selection_keyboard, cancel_keyboard
)
from database.models import DatabaseModels
from services.scheduler import PostScheduler
from config import ADMIN_ID

logger = logging.getLogger(__name__)
router = Router()


class SettingsStates(StatesGroup):
    waiting_for_custom_time = State()
    waiting_for_posts_limit = State()
    waiting_for_interval_minutes = State()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(F.text == "⚙️ Настройки")
async def show_settings_menu(message: Message):
    """Показ меню настроек"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⚙️ <b>Настройки бота</b>\n\n"
        "Здесь вы можете настроить различные параметры работы бота:",
        parse_mode="HTML",
        reply_markup=settings_keyboard()
    )


@router.callback_query(F.data == "schedule_settings")
async def show_schedule_settings(callback: CallbackQuery, db: DatabaseModels):
    """Показ настроек расписания"""
    try:
        # Получаем текущие настройки
        schedule_type = await db.get_setting("schedule_type") or "interval"

        if schedule_type == "times":
            times = await db.get_setting("schedule_times") or "09:00,15:00,21:00"
            current_info = f"Тип: По времени\nВремя: {times.replace(',', ', ')}"
        else:
            interval = await db.get_setting("schedule_interval") or "3"
            current_info = f"Тип: По интервалам\nИнтервал: каждые {interval} часа"

        text = f"""
⏰ <b>Настройки расписания</b>

<b>Текущие настройки:</b>
{current_info}

<b>Выберите тип расписания:</b>
• <b>По времени</b> - публикация в определенные часы
• <b>По интервалам</b> - публикация каждые N часов
        """

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=schedule_settings_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения настроек расписания: {str(e)}")
        await callback.answer("❌ Ошибка получения настроек")


@router.callback_query(F.data == "schedule_by_time")
async def setup_time_schedule(callback: CallbackQuery):
    """Настройка расписания по времени"""
    text = """
⏰ <b>Расписание по времени</b>

Выберите время для автоматической публикации.
Можно выбрать несколько вариантов.

<b>Рекомендуемые время:</b>
• <b>Утро:</b> 06:00 - 09:00
• <b>День:</b> 12:00 - 15:00  
• <b>Вечер:</b> 18:00 - 21:00

Выберите время из предложенных или укажите свое:
    """

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=time_selection_keyboard()
    )


@router.callback_query(F.data.startswith("time_"))
async def select_time(callback: CallbackQuery, db: DatabaseModels, scheduler: PostScheduler):
    """Выбор времени для расписания"""
    time_code = callback.data.split("_")[1]
    time_str = f"{time_code[:2]}:{time_code[2:]}"

    try:
        # Получаем текущие времена
        current_times = await db.get_setting("schedule_times") or ""
        times_list = [t.strip() for t in current_times.split(",") if t.strip()]

        if time_str in times_list:
            # Убираем время
            times_list.remove(time_str)
            action = "удалено"
        else:
            # Добавляем время
            times_list.append(time_str)
            action = "добавлено"

        # Сортируем времена
        times_list.sort()
        new_times = ",".join(times_list)

        # Сохраняем настройки
        await db.set_setting("schedule_type", "times")
        await db.set_setting("schedule_times", new_times)

        # Обновляем планировщик
        if times_list:
            scheduler.schedule_daily_posts(times_list)

        times_display = ", ".join(times_list) if times_list else "не выбрано"

        await callback.answer(f"✅ Время {time_str} {action}")

        # Обновляем сообщение
        text = f"""
⏰ <b>Расписание по времени</b>

<b>Выбранные времена:</b> {times_display}

Выберите дополнительное время или завершите настройку:
        """

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=time_selection_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка настройки времени: {str(e)}")
        await callback.answer("❌ Ошибка настройки времени")


@router.callback_query(F.data == "custom_time")
async def custom_time_input(callback: CallbackQuery, state: FSMContext):
    """Ввод пользовательского времени"""
    await state.set_state(SettingsStates.waiting_for_custom_time)

    await callback.message.edit_text(
        "⏰ <b>Свое время</b>\n\n"
        "Введите время в формате HH:MM (например: 14:30)\n"
        "Можно ввести несколько времен через запятую:\n"
        "<code>09:00, 14:30, 20:15</code>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )


@router.message(StateFilter(SettingsStates.waiting_for_custom_time))
async def process_custom_time(message: Message, state: FSMContext, db: DatabaseModels, scheduler: PostScheduler):
    """Обработка пользовательского времени"""
    if not is_admin(message.from_user.id):
        return

    time_input = message.text.strip()

    # Парсим времена
    import re
    time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'

    times_list = []
    for time_str in time_input.split(','):
        time_str = time_str.strip()
        if re.match(time_pattern, time_str):
            times_list.append(time_str)
        else:
            await message.answer(
                f"❌ <b>Неверный формат времени:</b> {time_str}\n\n"
                f"Используйте формат HH:MM (например: 14:30)",
                parse_mode="HTML"
            )
            return

    if not times_list:
        await message.answer(
            "❌ <b>Не указано корректное время</b>\n\n"
            "Введите время в формате HH:MM",
            parse_mode="HTML"
        )
        return

    try:
        # Сортируем и сохраняем
        times_list.sort()
        times_str = ",".join(times_list)

        await db.set_setting("schedule_type", "times")
        await db.set_setting("schedule_times", times_str)

        # Обновляем планировщик
        scheduler.schedule_daily_posts(times_list)

        await state.clear()

        await message.answer(
            f"✅ <b>Расписание установлено!</b>\n\n"
            f"<b>Времена публикации:</b> {', '.join(times_list)}\n\n"
            f"Бот будет автоматически публиковать посты в указанное время.",
            parse_mode="HTML",
            reply_markup=settings_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка сохранения времени: {str(e)}")
        await message.answer(
            "❌ <b>Ошибка сохранения</b>\n\n"
            "Попробуйте еще раз.",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "schedule_by_interval")
async def setup_interval_schedule(callback: CallbackQuery):
    """Настройка расписания по интервалам"""
    text = """
🔄 <b>Расписание по интервалам</b>

Выберите интервал между публикациями.
Бот будет автоматически публиковать посты через указанные промежутки времени.

<b>Рекомендации:</b>
• <b>1-2 часа</b> - для очень активных каналов
• <b>3-4 часа</b> - оптимально для большинства каналов
• <b>6-8 часов</b> - для спокойных каналов
• <b>12 часов</b> - минимальная активность

Выберите интервал:
    """

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=interval_selection_keyboard()
    )


@router.callback_query(F.data.startswith("interval_"))
async def select_interval(callback: CallbackQuery, db: DatabaseModels, scheduler: PostScheduler):
    """Выбор интервала для расписания"""
    interval_hours = callback.data.split("_")[1]

    try:
        # Сохраняем настройки
        await db.set_setting("schedule_type", "interval")
        await db.set_setting("schedule_interval", interval_hours)

        # Обновляем планировщик
        scheduler.schedule_interval_posts(int(interval_hours))

        await callback.message.edit_text(
            f"✅ <b>Интервал установлен!</b>\n\n"
            f"<b>Публикация каждые:</b> {interval_hours} часа\n\n"
            f"Бот будет автоматически публиковать посты через указанные интервалы.",
            parse_mode="HTML",
            reply_markup=schedule_settings_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка настройки интервала: {str(e)}")
        await callback.answer("❌ Ошибка настройки интервала")


@router.callback_query(F.data == "current_schedule")
async def show_current_schedule(callback: CallbackQuery, db: DatabaseModels, scheduler: PostScheduler):
    """Показ текущего расписания"""
    try:
        schedule_type = await db.get_setting("schedule_type") or "не настроено"

        if schedule_type == "times":
            times = await db.get_setting("schedule_times") or ""
            if times:
                times_list = times.split(",")
                schedule_info = f"<b>Тип:</b> По времени\n<b>Времена:</b> {', '.join(times_list)}"
            else:
                schedule_info = "<b>Тип:</b> По времени\n<b>Времена:</b> не настроены"
        elif schedule_type == "interval":
            interval = await db.get_setting("schedule_interval") or "не настроен"
            schedule_info = f"<b>Тип:</b> По интервалам\n<b>Интервал:</b> каждые {interval} часа"
        else:
            schedule_info = "<b>Расписание не настроено</b>"

        # Получаем информацию о запланированных задачах
        jobs = scheduler.get_scheduled_jobs()
        jobs_info = ""

        if jobs:
            jobs_info = "\n\n<b>Запланированные задачи:</b>\n"
            for i, job in enumerate(jobs[:3], 1):  # Показываем первые 3
                next_run = job.get('next_run', 'Неизвестно')
                jobs_info += f"{i}. Следующий запуск: {next_run}\n"

        text = f"""
📅 <b>Текущее расписание</b>

{schedule_info}
{jobs_info}

<b>Статус планировщика:</b> {'🟢 Работает' if scheduler.running else '🔴 Остановлен'}
        """

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=schedule_settings_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения расписания: {str(e)}")
        await callback.answer("❌ Ошибка получения расписания")


@router.callback_query(F.data == "style_settings")
async def show_style_settings(callback: CallbackQuery, db: DatabaseModels):
    """Показ настроек стиля"""
    try:
        current_style = await db.get_setting("default_style") or "engaging"

        style_descriptions = {
            "casual": "😊 Дружелюбный - неформальный, разговорный стиль",
            "neutral": "📰 Нейтральный - классический информационный стиль",
            "engaging": "🎯 Привлекательный - с эмодзи и призывами к действию",
            "formal": "👔 Официальный - деловой, строгий стиль"
        }

        current_desc = style_descriptions.get(current_style, "Неизвестный")

        text = f"""
🎨 <b>Настройки стиля постов</b>

<b>Текущий стиль:</b> {current_desc}

<b>Доступные стили:</b>

{chr(10).join(style_descriptions.values())}

Выберите новый стиль для обработки новостей:
        """

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=style_settings_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения настроек стиля: {str(e)}")
        await callback.answer("❌ Ошибка получения настроек")


@router.callback_query(F.data.startswith("style_"))
async def select_style(callback: CallbackQuery, db: DatabaseModels):
    """Выбор стиля обработки"""
    style = callback.data.split("_")[1]

    style_names = {
        "casual": "😊 Дружелюбный",
        "neutral": "📰 Нейтральный",
        "engaging": "🎯 Привлекательный",
        "formal": "👔 Официальный"
    }

    try:
        await db.set_setting("default_style", style)

        style_name = style_names.get(style, style)

        await callback.message.edit_text(
            f"✅ <b>Стиль изменен!</b>\n\n"
            f"<b>Новый стиль:</b> {style_name}\n\n"
            f"Все новые посты будут обрабатываться в выбранном стиле.",
            parse_mode="HTML",
            reply_markup=style_settings_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка изменения стиля: {str(e)}")
        await callback.answer("❌ Ошибка изменения стиля")


@router.callback_query(F.data == "limits_settings")
async def show_limits_settings(callback: CallbackQuery, db: DatabaseModels):
    """Показ настроек лимитов"""
    try:
        max_posts_per_day = await db.get_setting("max_posts_per_day") or "20"
        min_interval_minutes = await db.get_setting("min_interval_minutes") or "30"

        text = f"""
📊 <b>Настройки лимитов</b>

<b>Текущие лимиты:</b>
• Максимум постов в день: {max_posts_per_day}
• Минимальный интервал: {min_interval_minutes} минут

<b>Описание:</b>
• <b>Максимум постов в день</b> - общий лимит для всех каналов
• <b>Минимальный интервал</b> - минимальное время между публикациями

Отправьте команду для изменения:
<code>/maxposts [число]</code> - изменить максимум постов (1-50)
<code>/interval [минуты]</code> - изменить интервал (10-120 минут)
        """

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения лимитов: {str(e)}")
        await callback.answer("❌ Ошибка получения настроек")


@router.callback_query(F.data == "ai_settings")
async def show_ai_settings(callback: CallbackQuery, db: DatabaseModels):
    """Показ настроек ИИ"""
    try:
        creativity = await db.get_setting("ai_creativity") or "0.7"
        max_length = await db.get_setting("ai_max_length") or "800"
        language = await db.get_setting("ai_language") or "russian"

        text = f"""
🤖 <b>Настройки ИИ обработки</b>

<b>Текущие настройки:</b>
• Креативность: {creativity} (0.0-1.0)
• Максимальная длина: {max_length} символов
• Язык: {language}

<b>Описание параметров:</b>
• <b>Креативность</b> - насколько творчески ИИ переписывает тексты
• <b>Максимальная длина</b> - лимит символов в посте
• <b>Язык</b> - основной язык обработки

<b>Качество обработки:</b>
✅ Сохранение фактов
✅ Изменение структуры
✅ Добавление эмодзи
✅ Генерация хештегов

Отправьте команду для изменения:
<code>/creativity [0.1-1.0]</code> - изменить креативность
<code>/maxlength [200-1000]</code> - изменить длину
        """

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения настроек ИИ: {str(e)}")
        await callback.answer("❌ Ошибка получения настроек")


@router.callback_query(F.data == "notification_settings")
async def show_notification_settings(callback: CallbackQuery, db: DatabaseModels):
    """Показ настроек уведомлений"""
    try:
        notify_errors = await db.get_setting("notify_errors") or "true"
        notify_success = await db.get_setting("notify_success") or "false"
        notify_stats = await db.get_setting("notify_daily_stats") or "true"

        error_status = "✅ Включены" if notify_errors == "true" else "❌ Отключены"
        success_status = "✅ Включены" if notify_success == "true" else "❌ Отключены"
        stats_status = "✅ Включены" if notify_stats == "true" else "❌ Отключены"

        text = f"""
🔔 <b>Настройки уведомлений</b>

<b>Типы уведомлений:</b>

<b>Ошибки и проблемы:</b> {error_status}
• Ошибки парсинга новостей
• Проблемы с каналами
• Ошибки ИИ обработки

<b>Успешные публикации:</b> {success_status}
• Уведомления о каждой публикации
• Статистика по постам

<b>Ежедневная статистика:</b> {stats_status}
• Сводка за день
• Количество постов и просмотров

Выберите настройку для изменения:
        """

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{'🔴 Отключить' if notify_errors == 'true' else '🟢 Включить'} уведомления об ошибках",
                    callback_data="toggle_notify_errors"
                )],
                [InlineKeyboardButton(
                    text=f"{'🔴 Отключить' if notify_success == 'true' else '🟢 Включить'} уведомления о публикациях",
                    callback_data="toggle_notify_success"
                )],
                [InlineKeyboardButton(
                    text=f"{'🔴 Отключить' if notify_stats == 'true' else '🟢 Включить'} ежедневную статистику",
                    callback_data="toggle_notify_stats"
                )],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")]
            ]
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка получения настроек уведомлений: {str(e)}")
        await callback.answer("❌ Ошибка получения настроек")


@router.callback_query(F.data.startswith("toggle_notify_"))
async def toggle_notification(callback: CallbackQuery, db: DatabaseModels):
    """Переключение настроек уведомлений"""
    setting_name = callback.data.replace("toggle_", "")

    try:
        current_value = await db.get_setting(setting_name) or "false"
        new_value = "false" if current_value == "true" else "true"

        await db.set_setting(setting_name, new_value)

        setting_names = {
            "notify_errors": "уведомления об ошибках",
            "notify_success": "уведомления о публикациях",
            "notify_stats": "ежедневная статистика"
        }

        setting_display = setting_names.get(setting_name, setting_name)
        status = "включены" if new_value == "true" else "отключены"

        await callback.answer(f"✅ {setting_display.title()} {status}")

        # Обновляем отображение
        await show_notification_settings(callback, db)

    except Exception as e:
        logger.error(f"Ошибка переключения уведомлений: {str(e)}")
        await callback.answer("❌ Ошибка изменения настроек")


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Возврат к главному меню настроек"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки бота</b>\n\n"
        "Здесь вы можете настроить различные параметры работы бота:",
        parse_mode="HTML",
        reply_markup=settings_keyboard()
    )


# Обработчики команд настроек (для лимитов и ИИ)
@router.message(F.text.startswith("/maxposts "))
async def set_max_posts(message: Message, db: DatabaseModels):
    """Установка максимального количества постов"""
    if not is_admin(message.from_user.id):
        return

    try:
        max_posts = int(message.text.split()[1])
        if 1 <= max_posts <= 50:
            await db.set_setting("max_posts_per_day", str(max_posts))
            await message.answer(
                f"✅ Максимум постов в день установлен: {max_posts}",
                reply_markup=settings_keyboard()
            )
        else:
            await message.answer("❌ Число должно быть от 1 до 50")
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат. Используйте: /maxposts 20")


@router.message(F.text.startswith("/interval "))
async def set_min_interval(message: Message, db: DatabaseModels):
    """Установка минимального интервала"""
    if not is_admin(message.from_user.id):
        return

    try:
        interval = int(message.text.split()[1])
        if 10 <= interval <= 120:
            await db.set_setting("min_interval_minutes", str(interval))
            await message.answer(
                f"✅ Минимальный интервал установлен: {interval} минут",
                reply_markup=settings_keyboard()
            )
        else:
            await message.answer("❌ Интервал должен быть от 10 до 120 минут")
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат. Используйте: /interval 30")


@router.message(F.text.startswith("/creativity "))
async def set_creativity(message: Message, db: DatabaseModels):
    """Установка креативности ИИ"""
    if not is_admin(message.from_user.id):
        return

    try:
        creativity = float(message.text.split()[1])
        if 0.1 <= creativity <= 1.0:
            await db.set_setting("ai_creativity", str(creativity))
            await message.answer(
                f"✅ Креативность ИИ установлена: {creativity}",
                reply_markup=settings_keyboard()
            )
        else:
            await message.answer("❌ Значение должно быть от 0.1 до 1.0")
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат. Используйте: /creativity 0.7")


@router.message(F.text.startswith("/maxlength "))
async def set_max_length(message: Message, db: DatabaseModels):
    """Установка максимальной длины поста"""
    if not is_admin(message.from_user.id):
        return

    try:
        max_length = int(message.text.split()[1])
        if 200 <= max_length <= 1000:
            await db.set_setting("ai_max_length", str(max_length))
            await message.answer(
                f"✅ Максимальная длина поста установлена: {max_length} символов",
                reply_markup=settings_keyboard()
            )
        else:
            await message.answer("❌ Длина должна быть от 200 до 1000 символов")
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат. Используйте: /maxlength 800")