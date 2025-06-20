from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📺 Мои каналы")],
            [KeyboardButton(text="📰 Источники новостей"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🚀 Запустить публикацию"), KeyboardButton(text="⏹ Остановить бота")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def statistics_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура статистики"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Общая статистика", callback_data="stats_general")],
            [InlineKeyboardButton(text="📺 По каналам", callback_data="stats_channels")],
            [InlineKeyboardButton(text="📰 По источникам", callback_data="stats_sources")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )
    return keyboard


def publication_control_keyboard(is_running: bool) -> InlineKeyboardMarkup:
    """Клавиатура управления публикациями"""
    if is_running:
        main_button = InlineKeyboardButton(text="⏹ Остановить", callback_data="stop_publication")
        status_text = "🟢 Бот работает"
    else:
        main_button = InlineKeyboardButton(text="▶️ Запустить", callback_data="start_publication")
        status_text = "🔴 Бот остановлен"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=status_text, callback_data="publication_status")],
            [main_button],
            [InlineKeyboardButton(text="📝 Опубликовать сейчас", callback_data="publish_now")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )
    return keyboard


def help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура помощи"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Быстрый старт", callback_data="help_quickstart")],
            [InlineKeyboardButton(text="📺 Управление каналами", callback_data="help_channels")],
            [InlineKeyboardButton(text="📰 Источники новостей", callback_data="help_sources")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="help_settings")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )
    return keyboard


def confirmation_keyboard(action: str, item_id: str = "") -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{item_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")
            ]
        ]
    )
    return keyboard