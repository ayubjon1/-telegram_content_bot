# utils/keyboards.py - ПОЛНОСТЬЮ ОБНОВЛЕННЫЙ
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


# ========================================
# ГЛАВНЫЕ МЕНЮ
# ========================================

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню ИИ-агента с современным дизайном"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🤖 ИИ-Панель"),
                KeyboardButton(text="📊 Аналитика Pro")
            ],
            [
                KeyboardButton(text="📺 Каналы"),
                KeyboardButton(text="📰 Контент")
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
                KeyboardButton(text="🚀 Автопилот")
            ],
            [
                KeyboardButton(text="💡 ИИ-Помощник"),
                KeyboardButton(text="📈 Статус")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите раздел управления..."
    )
    return keyboard


def ai_control_panel_keyboard() -> InlineKeyboardMarkup:
    """ИИ панель управления - основной хаб"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧠 Анализ контента", callback_data="ai_content_analysis"),
                InlineKeyboardButton(text="🎨 Генерация", callback_data="ai_generation")
            ],
            [
                InlineKeyboardButton(text="🧪 A/B Тесты", callback_data="ai_ab_testing"),
                InlineKeyboardButton(text="🔮 Предсказания", callback_data="ai_predictions")
            ],
            [
                InlineKeyboardButton(text="🎯 Оптимизация", callback_data="ai_optimization"),
                InlineKeyboardButton(text="📊 ИИ-Метрики", callback_data="ai_metrics")
            ],
            [
                InlineKeyboardButton(text="🤖 Настройки ИИ", callback_data="ai_settings"),
                InlineKeyboardButton(text="🔄 Обучение", callback_data="ai_training")
            ],
            [
                InlineKeyboardButton(text="💬 Чат с ИИ", callback_data="ai_chat"),
                InlineKeyboardButton(text="📚 ИИ-База знаний", callback_data="ai_knowledge")
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


# ========================================
# АНАЛИТИКА И СТАТИСТИКА
# ========================================

def analytics_pro_keyboard() -> InlineKeyboardMarkup:
    """Расширенная аналитика"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 Dashboard", callback_data="analytics_dashboard"),
                InlineKeyboardButton(text="🎯 Engagement", callback_data="analytics_engagement")
            ],
            [
                InlineKeyboardButton(text="📊 Тренды", callback_data="analytics_trends"),
                InlineKeyboardButton(text="🔥 Вирусность", callback_data="analytics_viral")
            ],
            [
                InlineKeyboardButton(text="👥 Аудитория", callback_data="analytics_audience"),
                InlineKeyboardButton(text="💰 Монетизация", callback_data="analytics_money")
            ],
            [
                InlineKeyboardButton(text="📅 По периодам", callback_data="analytics_periods"),
                InlineKeyboardButton(text="🏆 Топ контент", callback_data="analytics_top")
            ],
            [
                InlineKeyboardButton(text="📋 Отчеты", callback_data="analytics_reports"),
                InlineKeyboardButton(text="🔄 Реалтайм", callback_data="analytics_realtime")
            ],
            [
                InlineKeyboardButton(text="⬇️ Экспорт", callback_data="analytics_export"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


def channels_management_keyboard() -> InlineKeyboardMarkup:
    """Управление каналами с расширенным функционалом"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Мои каналы", callback_data="list_channels"),
                InlineKeyboardButton(text="➕ Добавить", callback_data="add_channel")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="channels_stats"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="channels_settings")
            ],
            [
                InlineKeyboardButton(text="🎯 Автотаргетинг", callback_data="channels_targeting"),
                InlineKeyboardButton(text="🔄 Синхронизация", callback_data="channels_sync")
            ],
            [
                InlineKeyboardButton(text="🧪 Тест каналов", callback_data="channels_test"),
                InlineKeyboardButton(text="📈 Рост", callback_data="channels_growth")
            ],
            [
                InlineKeyboardButton(text="🎨 Брендинг", callback_data="channels_branding"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


# ========================================
# КОНТЕНТ И ГЕНЕРАЦИЯ
# ========================================

def content_management_keyboard() -> InlineKeyboardMarkup:
    """Управление контентом"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📰 Источники", callback_data="content_sources"),
                InlineKeyboardButton(text="🎨 Генерация", callback_data="content_generation")
            ],
            [
                InlineKeyboardButton(text="📝 Редактор", callback_data="content_editor"),
                InlineKeyboardButton(text="📅 Планировщик", callback_data="content_scheduler")
            ],
            [
                InlineKeyboardButton(text="🏷️ Теги и хештеги", callback_data="content_tags"),
                InlineKeyboardButton(text="🖼️ Медиа", callback_data="content_media")
            ],
            [
                InlineKeyboardButton(text="🔄 Репосты", callback_data="content_reposts"),
                InlineKeyboardButton(text="📊 Анализ", callback_data="content_analysis")
            ],
            [
                InlineKeyboardButton(text="🎯 Персонализация", callback_data="content_personalization"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


def ai_generation_keyboard() -> InlineKeyboardMarkup:
    """ИИ генерация контента"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍️ Текст", callback_data="generate_text"),
                InlineKeyboardButton(text="🖼️ Изображения", callback_data="generate_images")
            ],
            [
                InlineKeyboardButton(text="🎬 Видео", callback_data="generate_video"),
                InlineKeyboardButton(text="🎵 Аудио", callback_data="generate_audio")
            ],
            [
                InlineKeyboardButton(text="📊 Инфографика", callback_data="generate_infographic"),
                InlineKeyboardButton(text="🎭 Мемы", callback_data="generate_memes")
            ],
            [
                InlineKeyboardButton(text="📰 Новости", callback_data="generate_news"),
                InlineKeyboardButton(text="💡 Идеи", callback_data="generate_ideas")
            ],
            [
                InlineKeyboardButton(text="🎨 Стили", callback_data="generation_styles"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="generation_settings")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="ai_panel")
            ]
        ]
    )
    return keyboard


# ========================================
# АВТОПИЛОТ И ПЛАНИРОВЩИК
# ========================================

def autopilot_keyboard() -> InlineKeyboardMarkup:
    """Автопилот управление"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Запустить", callback_data="autopilot_start"),
                InlineKeyboardButton(text="⏹️ Остановить", callback_data="autopilot_stop")
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="autopilot_settings"),
                InlineKeyboardButton(text="📊 Статус", callback_data="autopilot_status")
            ],
            [
                InlineKeyboardButton(text="🎯 Сценарии", callback_data="autopilot_scenarios"),
                InlineKeyboardButton(text="🕐 Расписание", callback_data="autopilot_schedule")
            ],
            [
                InlineKeyboardButton(text="🧠 ИИ-Логика", callback_data="autopilot_ai_logic"),
                InlineKeyboardButton(text="🔄 Адаптация", callback_data="autopilot_adaptation")
            ],
            [
                InlineKeyboardButton(text="📈 Производительность", callback_data="autopilot_performance"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


def scheduler_keyboard() -> InlineKeyboardMarkup:
    """Планировщик с расширенными возможностями"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Календарь", callback_data="scheduler_calendar"),
                InlineKeyboardButton(text="⏰ Таймеры", callback_data="scheduler_timers")
            ],
            [
                InlineKeyboardButton(text="🎯 Умное планирование", callback_data="scheduler_smart"),
                InlineKeyboardButton(text="🔄 Автопланы", callback_data="scheduler_auto")
            ],
            [
                InlineKeyboardButton(text="📊 Аналитика времени", callback_data="scheduler_analytics"),
                InlineKeyboardButton(text="🎪 События", callback_data="scheduler_events")
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="scheduler_settings"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="content_management")
            ]
        ]
    )
    return keyboard


# ========================================
# НАСТРОЙКИ И КОНФИГУРАЦИЯ
# ========================================

def settings_keyboard() -> InlineKeyboardMarkup:
    """Главное меню настроек"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🤖 ИИ Настройки", callback_data="settings_ai"),
                InlineKeyboardButton(text="🎨 Интерфейс", callback_data="settings_ui")
            ],
            [
                InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications"),
                InlineKeyboardButton(text="🔐 Безопасность", callback_data="settings_security")
            ],
            [
                InlineKeyboardButton(text="📊 Аналитика", callback_data="settings_analytics"),
                InlineKeyboardButton(text="🔄 Интеграции", callback_data="settings_integrations")
            ],
            [
                InlineKeyboardButton(text="💾 Бэкапы", callback_data="settings_backups"),
                InlineKeyboardButton(text="🌐 API", callback_data="settings_api")
            ],
            [
                InlineKeyboardButton(text="📋 Экспорт/Импорт", callback_data="settings_export"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


# ========================================
# НОВОСТИ И ИСТОЧНИКИ
# ========================================

def news_sources_keyboard() -> InlineKeyboardMarkup:
    """Управление источниками новостей"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Список источников", callback_data="list_sources"),
                InlineKeyboardButton(text="➕ Добавить источник", callback_data="add_source")
            ],
            [
                InlineKeyboardButton(text="🧪 Тест парсинга", callback_data="test_parsing"),
                InlineKeyboardButton(text="🔄 Обновить все", callback_data="refresh_sources")
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="sources_settings"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="sources_stats")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


def source_list_keyboard(sources: List[Dict]) -> InlineKeyboardMarkup:
    """Список источников с кнопками"""
    buttons = []

    for source in sources[:10]:  # Показываем максимум 10
        status_emoji = "✅" if source['is_active'] else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {source['name']}",
                callback_data=f"source_{source['id']}"
            )
        ])

    # Навигация
    buttons.append([
        InlineKeyboardButton(text="➕ Добавить новый", callback_data="add_source"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_sources")
    ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Источники", callback_data="back_to_sources")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channel_list_keyboard(channels: List[Dict]) -> InlineKeyboardMarkup:
    """Список каналов с кнопками"""
    buttons = []

    for channel in channels[:10]:  # Показываем максимум 10
        status_emoji = "🟢" if channel['is_active'] else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {channel['channel_name']}",
                callback_data=f"channel_{channel['channel_id']}"
            )
        ])

    # Навигация
    buttons.append([
        InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="channels_settings")
    ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Каналы", callback_data="back_to_channels")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channel_actions_keyboard(channel_id: str, is_active: bool) -> InlineKeyboardMarkup:
    """Действия с каналом"""
    toggle_text = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    toggle_action = f"deactivate_{channel_id}" if is_active else f"activate_{channel_id}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data=f"stats_{channel_id}"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data=f"settings_{channel_id}")
            ],
            [
                InlineKeyboardButton(text="🧪 Тест поста", callback_data=f"test_post_{channel_id}"),
                InlineKeyboardButton(text=toggle_text, callback_data=toggle_action)
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить канал", callback_data=f"delete_{channel_id}"),
                InlineKeyboardButton(text="🔙 Список", callback_data="list_channels")
            ]
        ]
    )
    return keyboard


# ========================================
# ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ
# ========================================

def quick_actions_keyboard() -> InlineKeyboardMarkup:
    """Быстрые действия"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡ Опубликовать сейчас", callback_data="quick_publish"),
                InlineKeyboardButton(text="🧠 Анализ текста", callback_data="quick_analyze")
            ],
            [
                InlineKeyboardButton(text="🎨 Генерация", callback_data="quick_generate"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="quick_stats")
            ],
            [
                InlineKeyboardButton(text="🔧 Диагностика", callback_data="quick_health"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="quick_refresh")
            ]
        ]
    )
    return keyboard


def confirmation_keyboard(action: str, item_id: str = "", context: str = "") -> InlineKeyboardMarkup:
    """Улучшенная клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, выполнить",
                    callback_data=f"confirm_{action}_{item_id}_{context}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"cancel_{action}_{context}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="ℹ️ Подробнее",
                    callback_data=f"info_{action}_{context}"
                )
            ]
        ]
    )
    return keyboard


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура отмены"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
        ]
    )


# ========================================
# СПЕЦИАЛИЗИРОВАННЫЕ КЛАВИАТУРЫ
# ========================================

def ai_chat_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для чата с ИИ"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💡 Идеи контента", callback_data="ai_chat_ideas"),
                InlineKeyboardButton(text="📊 Анализ", callback_data="ai_chat_analysis")
            ],
            [
                InlineKeyboardButton(text="🎯 Стратегия", callback_data="ai_chat_strategy"),
                InlineKeyboardButton(text="📈 Прогнозы", callback_data="ai_chat_forecast")
            ],
            [
                InlineKeyboardButton(text="🔧 Оптимизация", callback_data="ai_chat_optimize"),
                InlineKeyboardButton(text="❓ Вопрос", callback_data="ai_chat_question")
            ],
            [
                InlineKeyboardButton(text="📚 История", callback_data="ai_chat_history"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="ai_panel")
            ]
        ]
    )
    return keyboard


def ab_testing_keyboard() -> InlineKeyboardMarkup:
    """A/B тестирование"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧪 Новый тест", callback_data="ab_new_test"),
                InlineKeyboardButton(text="📊 Активные", callback_data="ab_active_tests")
            ],
            [
                InlineKeyboardButton(text="📈 Результаты", callback_data="ab_results"),
                InlineKeyboardButton(text="🏆 Победители", callback_data="ab_winners")
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="ab_settings"),
                InlineKeyboardButton(text="📚 История", callback_data="ab_history")
            ],
            [
                InlineKeyboardButton(text="💡 Рекомендации", callback_data="ab_recommendations"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="ai_panel")
            ]
        ]
    )
    return keyboard


def status_dashboard_keyboard(system_status: dict) -> InlineKeyboardMarkup:
    """Динамическая клавиатура статуса"""
    # Определяем статус эмодзи
    status_emoji = {
        'healthy': '🟢',
        'warning': '🟡',
        'error': '🟠',
        'critical': '🔴'
    }

    current_emoji = status_emoji.get(system_status.get('status', 'error'), '❓')

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{current_emoji} Система: {system_status.get('status', 'Unknown').upper()}",
                    callback_data="status_system"
                )
            ],
            [
                InlineKeyboardButton(text="🤖 ИИ Компоненты", callback_data="status_ai"),
                InlineKeyboardButton(text="📊 Метрики", callback_data="status_metrics")
            ],
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="status_refresh"),
                InlineKeyboardButton(text="🛠️ Исцеление", callback_data="status_heal")
            ],
            [
                InlineKeyboardButton(text="📋 Логи", callback_data="status_logs"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


# ========================================
# УПРАВЛЕНИЕ ИИ
# ========================================

def ai_management_keyboard() -> InlineKeyboardMarkup:
    """Полное управление ИИ"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧠 Настройки ИИ", callback_data="ai_config"),
                InlineKeyboardButton(text="📝 Форматы постов", callback_data="post_formats")
            ],
            [
                InlineKeyboardButton(text="📺 Управление каналами", callback_data="manage_channels"),
                InlineKeyboardButton(text="📰 Управление источниками", callback_data="manage_sources")
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
                InlineKeyboardButton(text="💾 Экспорт/Импорт", callback_data="ai_export_import")
            ],
            [
                InlineKeyboardButton(text="🔄 Обновить статус", callback_data="refresh_ai_status"),
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard


# ========================================
# ПАГИНАЦИЯ И СПИСКИ
# ========================================

def paginated_keyboard(items: List[Dict], page: int = 0, per_page: int = 5,
                       action_prefix: str = "item", back_action: str = "back") -> InlineKeyboardMarkup:
    """Универсальная пагинация"""
    total_pages = (len(items) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(items))

    buttons = []

    # Элементы текущей страницы
    for i in range(start_idx, end_idx):
        item = items[i]
        buttons.append([
            InlineKeyboardButton(
                text=f"{item.get('emoji', '•')} {item.get('name', f'Item {i + 1}')}",
                callback_data=f"{action_prefix}_{item.get('id', i)}"
            )
        ])

    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{action_prefix}_{page - 1}")
        )

    nav_buttons.append(
        InlineKeyboardButton(text=f"📄 {page + 1}/{total_pages}", callback_data="page_info")
    )

    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️ Далее", callback_data=f"page_{action_prefix}_{page + 1}")
        )

    if nav_buttons:
        buttons.append(nav_buttons)

    # Кнопка возврата
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data=back_action)
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ========================================
# АДАПТИВНЫЕ КЛАВИАТУРЫ
# ========================================

def adaptive_main_menu(user_level: str = "beginner") -> ReplyKeyboardMarkup:
    """Адаптивное главное меню в зависимости от уровня пользователя"""

    if user_level == "beginner":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚀 Быстрый старт")],
                [KeyboardButton(text="📺 Мои каналы"), KeyboardButton(text="📰 Контент")],
                [KeyboardButton(text="📊 Простая статистика")],
                [KeyboardButton(text="❓ Помощь")]
            ],
            resize_keyboard=True
        )
    elif user_level == "advanced":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🤖 ИИ-Панель"), KeyboardButton(text="📊 Аналитика Pro")],
                [KeyboardButton(text="📺 Каналы"), KeyboardButton(text="📰 Контент")],
                [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🚀 Автопилот")],
                [KeyboardButton(text="🧪 Эксперименты"), KeyboardButton(text="📈 Статус")]
            ],
            resize_keyboard=True
        )
    else:  # expert
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🧠 ИИ-Ядро"), KeyboardButton(text="⚡ Терминал")],
                [KeyboardButton(text="📊 Analytics++"), KeyboardButton(text="🔬 Лаборатория")],
                [KeyboardButton(text="🛠️ DevTools"), KeyboardButton(text="🌐 API")],
                [KeyboardButton(text="📈 Мониторинг"), KeyboardButton(text="🔧 Конфиг")]
            ],
            resize_keyboard=True
        )

    return keyboard