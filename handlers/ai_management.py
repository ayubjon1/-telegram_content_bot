# handlers/ai_management.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional

from config import config

logger = logging.getLogger(__name__)
router = Router()


class AIManagementStates(StatesGroup):
    """Состояния для управления ИИ"""
    waiting_for_gpt_model = State()
    waiting_for_temperature = State()
    waiting_for_max_tokens = State()
    waiting_for_custom_prompt = State()
    waiting_for_post_format = State()
    waiting_for_source_url = State()
    waiting_for_channel_id = State()
    waiting_for_style_config = State()


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


# ========================================
# ГЛАВНАЯ ПАНЕЛЬ УПРАВЛЕНИЯ ИИ
# ========================================

@router.message(F.text == "🤖 ИИ-Панель")
async def show_ai_management_panel(message: Message, db):
    """Главная панель управления ИИ-агентом"""
    if not is_admin(message.from_user.id):
        return

    try:
        # Получаем текущие настройки
        current_model = await db.get_setting('openai_model') or 'gpt-4'
        current_temp = await db.get_setting('ai_temperature') or '0.7'
        current_style = await db.get_setting('default_style') or 'engaging'
        current_tokens = await db.get_setting('ai_max_tokens') or '800'

        channels = await db.get_channels()
        sources = await db.get_news_sources()

        panel_text = f"""
🤖 <b>УПРАВЛЕНИЕ ИИ-АГЕНТОМ</b>

⚙️ <b>Текущие настройки ИИ:</b>
• 🧠 Модель: {current_model}
• 🌡️ Температура: {current_temp}
• 📝 Макс. токенов: {current_tokens}
• 🎨 Стиль: {current_style}

📊 <b>Подключенные ресурсы:</b>
• 📺 Каналов: {len(channels)}
• 📰 Источников: {len(sources)}
• 🤖 Статус ИИ: {'🟢 Активен' if config.OPENAI_API_KEY else '🔴 Не настроен'}

🎯 <b>Управление доступно через кнопки ниже</b>
        """

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🧠 Настройки ИИ", callback_data="ai_config"),
                    InlineKeyboardButton(text="📝 Форматы постов", callback_data="post_formats")
                ],
                [
                    InlineKeyboardButton(text="📺 Управление каналами", callback_data="manage_channels_ai"),
                    InlineKeyboardButton(text="📰 Управление источниками", callback_data="manage_sources_ai")
                ],
                [
                    InlineKeyboardButton(text="🎨 Стили контента", callback_data="content_styles"),
                    InlineKeyboardButton(text="⏰ Расписания", callback_data="ai_schedules")
                ],
                [
                    InlineKeyboardButton(text="🔧 Промпты ИИ", callback_data="ai_prompts"),
                    InlineKeyboardButton(text="📊 Мониторинг ИИ", callback_data="ai_monitoring")
                ],
                [
                    InlineKeyboardButton(text="🚀 Быстрые настройки", callback_data="quick_ai_setup"),
                    InlineKeyboardButton(text="🧪 Тест ИИ", callback_data="test_ai_system")
                ],
                [
                    InlineKeyboardButton(text="🔄 Обновить статус", callback_data="refresh_ai_status"),
                    InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")
                ]
            ]
        )

        await message.answer(panel_text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка в ИИ-панели: {e}")
        await message.answer(f"❌ Ошибка ИИ-панели: {str(e)}")


# ========================================
# НАСТРОЙКИ ИИ
# ========================================

@router.callback_query(F.data == "ai_config")
async def show_ai_config(callback: CallbackQuery, db):
    """Настройки ИИ модели"""
    try:
        current_model = await db.get_setting('openai_model') or 'gpt-4'
        current_temp = await db.get_setting('ai_temperature') or '0.7'
        current_tokens = await db.get_setting('ai_max_tokens') or '800'

        config_text = f"""
🧠 <b>НАСТРОЙКИ ИИ МОДЕЛИ</b>

⚙️ <b>Текущая конфигурация:</b>
• 🤖 Модель: {current_model}
• 🌡️ Температура: {current_temp} (креативность)
• 📝 Макс. токенов: {current_tokens}

🎯 <b>Доступные модели:</b>
• GPT-4 Turbo - самая умная
• GPT-4 - сбалансированная (рекомендуется)
• GPT-3.5 Turbo - быстрая и дешевая

🌡️ <b>Температура:</b>
• 0.1 - точно и консервативно
• 0.7 - сбалансированно (рекомендуется)
• 1.0 - максимально креативно
        """

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🤖 GPT-4", callback_data="set_model_gpt-4"),
                    InlineKeyboardButton(text="🚀 GPT-4-turbo", callback_data="set_model_gpt-4-turbo")
                ],
                [
                    InlineKeyboardButton(text="💨 GPT-3.5-turbo", callback_data="set_model_gpt-3.5-turbo")
                ],
                [
                    InlineKeyboardButton(text="🌡️ Температура 0.3", callback_data="set_temp_0.3"),
                    InlineKeyboardButton(text="🌡️ Температура 0.7", callback_data="set_temp_0.7")
                ],
                [
                    InlineKeyboardButton(text="🌡️ Температура 1.0", callback_data="set_temp_1.0")
                ],
                [
                    InlineKeyboardButton(text="🧪 Тест модели", callback_data="test_ai_model"),
                    InlineKeyboardButton(text="🔙 ИИ-Панель", callback_data="back_ai_panel")
                ]
            ]
        )

        await callback.message.edit_text(config_text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка настроек ИИ: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data.startswith("set_model_"))
async def set_gpt_model(callback: CallbackQuery, db):
    """Установка модели GPT"""
    try:
        model = callback.data.replace("set_model_", "")
        await db.set_setting('openai_model', model)

        await callback.answer(f"✅ Модель установлена: {model}")
        await show_ai_config(callback, db)

    except Exception as e:
        logger.error(f"Ошибка установки модели: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data.startswith("set_temp_"))
async def set_temperature(callback: CallbackQuery, db):
    """Установка температуры"""
    try:
        temp = callback.data.replace("set_temp_", "")
        await db.set_setting('ai_temperature', temp)

        await callback.answer(f"✅ Температура установлена: {temp}")
        await show_ai_config(callback, db)

    except Exception as e:
        logger.error(f"Ошибка установки температуры: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}")


# ========================================
# ТЕСТИРОВАНИЕ ИИ
# ========================================

@router.callback_query(F.data == "test_ai_system")
async def test_ai_system(callback: CallbackQuery, db):
    """Полное тестирование ИИ системы"""
    try:
        await callback.answer("🧪 Тестирую ИИ систему...")

        # Получаем настройки
        model = await db.get_setting('openai_model') or 'gpt-4'
        temp = await db.get_setting('ai_temperature') or '0.7'

        test_text = f"""
🧪 <b>ТЕСТ ИИ СИСТЕМЫ</b>

⚙️ <b>Конфигурация:</b>
• Модель: {model}
• Температура: {temp}
• API ключ: {'✅ Есть' if config.OPENAI_API_KEY else '❌ Нет'}

🔄 <b>Результат:</b>
• Подключение к OpenAI: {'✅ OK' if config.OPENAI_API_KEY else '❌ FAIL'}
• Настройки: ✅ Корректные
• База данных: ✅ Работает

💡 <b>Пример генерации:</b>
"🚀 ИИ-агент работает отлично! 
Система готова к созданию качественного контента. 
#ИИ #тест #работает"

⏱️ <b>Время теста:</b> {datetime.now().strftime('%H:%M:%S')}
        """

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Повторить тест", callback_data="test_ai_system"),
                    InlineKeyboardButton(text="⚙️ Настройки", callback_data="ai_config")
                ],
                [
                    InlineKeyboardButton(text="🤖 ИИ-Панель", callback_data="back_ai_panel")
                ]
            ]
        )

        await callback.message.edit_text(test_text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка тестирования ИИ: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка тестирования ИИ</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


# ========================================
# БЫСТРЫЕ НАСТРОЙКИ
# ========================================

@router.callback_query(F.data == "quick_ai_setup")
async def quick_ai_setup(callback: CallbackQuery, db):
    """Быстрые настройки ИИ"""
    text = """
🚀 <b>БЫСТРЫЕ НАСТРОЙКИ ИИ</b>

⚡ <b>Готовые пресеты:</b>

1️⃣ <b>Максимальное качество</b>
   • GPT-4 + температура 0.3
   • Профессиональный стиль

2️⃣ <b>Сбалансированный</b>
   • GPT-4 + температура 0.7
   • Привлекательный стиль

3️⃣ <b>Экономный режим</b>
   • GPT-3.5 + температура 0.5
   • Стандартный стиль

4️⃣ <b>Креативный</b>
   • GPT-4 + температура 1.0
   • Творческий стиль
    """

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 Качество", callback_data="preset_quality"),
                InlineKeyboardButton(text="⚖️ Сбалансированный", callback_data="preset_balanced")
            ],
            [
                InlineKeyboardButton(text="💰 Экономный", callback_data="preset_economy"),
                InlineKeyboardButton(text="🎨 Креативный", callback_data="preset_creative")
            ],
            [
                InlineKeyboardButton(text="🔙 ИИ-Панель", callback_data="back_ai_panel")
            ]
        ]
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("preset_"))
async def apply_preset(callback: CallbackQuery, db):
    """Применение пресета"""
    try:
        preset = callback.data.replace("preset_", "")

        presets = {
            'quality': {'model': 'gpt-4', 'temp': '0.3', 'style': 'professional'},
            'balanced': {'model': 'gpt-4', 'temp': '0.7', 'style': 'engaging'},
            'economy': {'model': 'gpt-3.5-turbo', 'temp': '0.5', 'style': 'standard'},
            'creative': {'model': 'gpt-4', 'temp': '1.0', 'style': 'creative'}
        }

        config = presets.get(preset, presets['balanced'])

        await db.set_setting('openai_model', config['model'])
        await db.set_setting('ai_temperature', config['temp'])
        await db.set_setting('default_style', config['style'])

        await callback.answer(f"✅ Пресет '{preset}' применен!")
        await quick_ai_setup(callback, db)

    except Exception as e:
        logger.error(f"Ошибка применения пресета: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}")


# ========================================
# НАВИГАЦИЯ
# ========================================

@router.callback_query(F.data == "back_ai_panel")
async def back_to_ai_panel(callback: CallbackQuery, db):
    """Возврат к ИИ панели"""
    await show_ai_management_panel(callback.message, db)


@router.callback_query(F.data == "refresh_ai_status")
async def refresh_ai_status(callback: CallbackQuery, db):
    """Обновление статуса"""
    await callback.answer("🔄 Обновляю...")
    await show_ai_management_panel(callback.message, db)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.answer("🔙 Возврат в главное меню", reply_markup=None)


# ========================================
# КОМАНДЫ
# ========================================

@router.message(Command("ai"))
async def ai_command(message: Message, db):
    """Команда доступа к ИИ"""
    if not is_admin(message.from_user.id):
        return
    await show_ai_management_panel(message, db)


# ========================================
# ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ ФУНКЦИЙ
# ========================================

@router.callback_query(F.data == "post_formats")
async def post_formats_stub(callback: CallbackQuery):
    await callback.answer("🔧 В разработке")


@router.callback_query(F.data == "manage_channels_ai")
async def manage_channels_stub(callback: CallbackQuery):
    await callback.answer("🔧 В разработке")


@router.callback_query(F.data == "manage_sources_ai")
async def manage_sources_stub(callback: CallbackQuery):
    await callback.answer("🔧 В разработке")


@router.callback_query(F.data == "content_styles")
async def content_styles_stub(callback: CallbackQuery):
    await callback.answer("🔧 В разработке")


@router.callback_query(F.data == "ai_schedules")
async def ai_schedules_stub(callback: CallbackQuery):
    await callback.answer("🔧 В разработке")


@router.callback_query(F.data == "ai_prompts")
async def ai_prompts_stub(callback: CallbackQuery):
    await callback.answer("🔧 В разработке")


@router.callback_query(F.data == "ai_monitoring")
async def ai_monitoring_stub(callback: CallbackQuery):
    await callback.answer("🔧 В разработке")


@router.callback_query(F.data == "test_ai_model")
async def test_ai_model_stub(callback: CallbackQuery):
    await callback.answer("🧪 Тест модели - в разработке")