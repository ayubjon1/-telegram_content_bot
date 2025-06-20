from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from utils.keyboards import (
    news_sources_keyboard, source_list_keyboard,
    cancel_keyboard, main_menu_keyboard
)
from database.models import DatabaseModels
from services.news_parser import NewsParser
from config import ADMIN_ID, NEWS_CATEGORIES

logger = logging.getLogger(__name__)
router = Router()


class NewsStates(StatesGroup):
    waiting_for_source_name = State()
    waiting_for_source_url = State()
    waiting_for_source_category = State()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(F.text == "📰 Источники новостей")
async def show_news_sources_menu(message: Message):
    """Показ меню управления источниками новостей"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📰 <b>Управление источниками новостей</b>\n\n"
        "Здесь вы можете добавлять и настраивать источники новостей для автоматического парсинга.\n\n"
        "Поддерживаются RSS ленты новостных сайтов.",
        parse_mode="HTML",
        reply_markup=news_sources_keyboard()
    )


@router.callback_query(F.data == "list_sources")
async def show_sources_list(callback: CallbackQuery, db: DatabaseModels):
    """Показ списка источников новостей"""
    try:
        sources = await db.get_news_sources()

        if not sources:
            await callback.message.edit_text(
                "📰 <b>Источники новостей</b>\n\n"
                "❌ У вас пока нет добавленных источников.\n"
                "Нажмите кнопку ниже, чтобы добавить первый источник.",
                parse_mode="HTML",
                reply_markup=news_sources_keyboard()
            )
            return

        text = "📰 <b>Ваши источники новостей:</b>\n\n"
        for source in sources:
            status = "✅" if source['is_active'] else "❌"
            text += f"{status} <b>{source['name']}</b>\n"
            text += f"Категория: {source['category']}\n"
            text += f"URL: <code>{source['url'][:50]}{'...' if len(source['url']) > 50 else ''}</code>\n\n"

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=source_list_keyboard(sources)
        )

    except Exception as e:
        logger.error(f"Ошибка получения списка источников: {str(e)}")
        await callback.answer("❌ Ошибка получения списка источников")


@router.callback_query(F.data == "add_source")
async def start_add_source(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления источника новостей"""
    await state.set_state(NewsStates.waiting_for_source_name)

    await callback.message.edit_text(
        "➕ <b>Добавление источника новостей</b>\n\n"
        "Отправьте название источника (например: 'Lenta.ru', 'РИА Новости'):",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )


@router.message(StateFilter(NewsStates.waiting_for_source_name))
async def process_source_name(message: Message, state: FSMContext):
    """Обработка названия источника"""
    if not is_admin(message.from_user.id):
        return

    source_name = message.text.strip()

    if len(source_name) < 2:
        await message.answer(
            "❌ <b>Слишком короткое название</b>\n\n"
            "Введите название длиной минимум 2 символа.",
            parse_mode="HTML"
        )
        return

    await state.update_data({'source_name': source_name})
    await state.set_state(NewsStates.waiting_for_source_url)

    await message.answer(
        f"✅ <b>Название принято:</b> {source_name}\n\n"
        f"Теперь отправьте URL RSS ленты.\n\n"
        f"<b>Примеры RSS лент:</b>\n"
        f"• https://lenta.ru/rss\n"
        f"• https://ria.ru/export/rss2/archive/index.xml\n"
        f"• https://tass.ru/rss/v2.xml",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )


@router.message(StateFilter(NewsStates.waiting_for_source_url))
async def process_source_url(message: Message, state: FSMContext):
    """Обработка URL источника"""
    if not is_admin(message.from_user.id):
        return

    source_url = message.text.strip()

    # Простая валидация URL
    if not (source_url.startswith('http://') or source_url.startswith('https://')):
        await message.answer(
            "❌ <b>Неверный формат URL</b>\n\n"
            "URL должен начинаться с http:// или https://",
            parse_mode="HTML"
        )
        return

    # Тестируем доступность RSS ленты
    test_result = await test_rss_feed(source_url)
    if not test_result['success']:
        await message.answer(
            f"❌ <b>Ошибка доступа к RSS ленте</b>\n\n"
            f"Не удалось загрузить RSS с адреса:\n"
            f"<code>{source_url}</code>\n\n"
            f"Ошибка: {test_result['error']}\n\n"
            f"Проверьте правильность URL.",
            parse_mode="HTML"
        )
        return

    await state.update_data({'source_url': source_url})
    await state.set_state(NewsStates.waiting_for_source_category)

    # Показываем категории
    categories_text = "\n".join([f"• {cat}" for cat in NEWS_CATEGORIES])

    await message.answer(
        f"✅ <b>URL принят и проверен!</b>\n"
        f"Найдено новостей: {test_result['news_count']}\n\n"
        f"Выберите категорию для источника:\n\n"
        f"{categories_text}\n\n"
        f"Отправьте название категории или 'общее' для смешанных новостей:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )


@router.message(StateFilter(NewsStates.waiting_for_source_category))
async def process_source_category(message: Message, state: FSMContext, db: DatabaseModels):
    """Обработка категории источника"""
    if not is_admin(message.from_user.id):
        return

    category = message.text.strip().lower()

    if category not in NEWS_CATEGORIES and category != 'общее':
        categories_text = ", ".join(NEWS_CATEGORIES)
        await message.answer(
            f"❌ <b>Неверная категория</b>\n\n"
            f"Доступные категории: {categories_text}, общее",
            parse_mode="HTML"
        )
        return

    # Получаем данные из состояния
    data = await state.get_data()
    source_name = data['source_name']
    source_url = data['source_url']

    try:
        # Сохраняем источник в базу данных
        await db.add_news_source(source_name, source_url, 'rss', category)

        await state.clear()

        await message.answer(
            f"✅ <b>Источник успешно добавлен!</b>\n\n"
            f"<b>Название:</b> {source_name}\n"
            f"<b>URL:</b> <code>{source_url}</code>\n"
            f"<b>Категория:</b> {category}\n\n"
            f"Источник готов к работе!",
            parse_mode="HTML",
            reply_markup=news_sources_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка добавления источника: {str(e)}")
        await message.answer(
            "❌ <b>Ошибка добавления источника</b>\n\n"
            "Попробуйте еще раз или обратитесь к администратору.",
            parse_mode="HTML"
        )


async def test_rss_feed(url: str) -> dict:
    """Тестирование RSS ленты"""
    try:
        async with NewsParser() as parser:
            news_items = await parser.parse_rss_feed(url, "Test Source")
            return {
                'success': True,
                'news_count': len(news_items),
                'error': None
            }
    except Exception as e:
        return {
            'success': False,
            'news_count': 0,
            'error': str(e)
        }


@router.callback_query(F.data == "test_parsing")
async def test_all_sources(callback: CallbackQuery, db: DatabaseModels):
    """Тестирование парсинга всех источников"""
    try:
        await callback.message.edit_text(
            "🧪 <b>Тестирование источников...</b>\n\n"
            "Проверяю доступность всех RSS лент...",
            parse_mode="HTML"
        )

        sources = await db.get_news_sources()
        if not sources:
            await callback.message.edit_text(
                "❌ <b>Нет источников для тестирования</b>\n\n"
                "Добавьте источники новостей для проведения теста.",
                parse_mode="HTML",
                reply_markup=news_sources_keyboard()
            )
            return

        results = []
        total_news = 0

        async with NewsParser() as parser:
            for source in sources:
                try:
                    news_items = await parser.parse_rss_feed(
                        source['url'],
                        source['name']
                    )
                    news_count = len(news_items)
                    total_news += news_count

                    status = "✅" if news_count > 0 else "⚠️"
                    results.append(f"{status} <b>{source['name']}</b>: {news_count} новостей")

                except Exception as e:
                    results.append(f"❌ <b>{source['name']}</b>: Ошибка - {str(e)[:50]}")

        result_text = f"""
🧪 <b>Результаты тестирования</b>

<b>Всего источников:</b> {len(sources)}
<b>Всего новостей:</b> {total_news}

<b>Детали по источникам:</b>
{chr(10).join(results)}

<b>Рекомендации:</b>
• ✅ - Источник работает отлично
• ⚠️ - Источник доступен, но новостей мало
• ❌ - Источник недоступен или ошибка
        """

        await callback.message.edit_text(
            result_text,
            parse_mode="HTML",
            reply_markup=news_sources_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка тестирования источников: {str(e)}")
        await callback.message.edit_text(
            "❌ <b>Ошибка тестирования</b>\n\n"
            "Не удалось протестировать источники.",
            parse_mode="HTML",
            reply_markup=news_sources_keyboard()
        )


@router.callback_query(F.data.startswith("source_"))
async def show_source_details(callback: CallbackQuery, db: DatabaseModels):
    """Показ деталей источника новостей"""
    source_id = int(callback.data.split("_")[1])

    try:
        sources = await db.get_news_sources()
        source = next((src for src in sources if src['id'] == source_id), None)

        if not source:
            await callback.answer("❌ Источник не найден")
            return

        # Тестируем источник
        test_result = await test_rss_feed(source['url'])

        status = "✅ Активен" if source['is_active'] else "❌ Неактивен"
        test_status = "✅ Работает" if test_result['success'] else "❌ Недоступен"

        text = f"""
📰 <b>{source['name']}</b>

<b>URL:</b> <code>{source['url']}</code>
<b>Категория:</b> {source['category']}
<b>Тип:</b> {source['source_type'].upper()}
<b>Статус:</b> {status}
<b>Доступность:</b> {test_status}

<b>Последний тест:</b>
Новостей найдено: {test_result['news_count']}
{f"Ошибка: {test_result['error']}" if test_result['error'] else ""}

Выберите действие:
        """

        # Создаем клавиатуру действий
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        toggle_text = "🔴 Деактивировать" if source['is_active'] else "🟢 Активировать"
        toggle_action = f"deactivate_source_{source_id}" if source['is_active'] else f"activate_source_{source_id}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🧪 Тест парсинга", callback_data=f"test_source_{source_id}")],
                [InlineKeyboardButton(text=toggle_text, callback_data=toggle_action)],
                [InlineKeyboardButton(text="🗑 Удалить источник", callback_data=f"delete_source_{source_id}")],
                [InlineKeyboardButton(text="🔙 К списку источников", callback_data="list_sources")]
            ]
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка получения данных источника: {str(e)}")
        await callback.answer("❌ Ошибка получения данных источника")


@router.callback_query(F.data.startswith("test_source_"))
async def test_single_source(callback: CallbackQuery, db: DatabaseModels):
    """Тестирование одного источника"""
    source_id = int(callback.data.split("_")[2])

    try:
        sources = await db.get_news_sources()
        source = next((src for src in sources if src['id'] == source_id), None)

        if not source:
            await callback.answer("❌ Источник не найден")
            return

        await callback.message.edit_text(
            f"🧪 <b>Тестирование источника</b>\n\n"
            f"Проверяю: {source['name']}...",
            parse_mode="HTML"
        )

        # Подробное тестирование
        async with NewsParser() as parser:
            news_items = await parser.parse_rss_feed(source['url'], source['name'])

        if news_items:
            # Показываем примеры новостей
            examples = []
            for i, news in enumerate(news_items[:3]):
                examples.append(f"{i + 1}. {news['title'][:60]}...")

            examples_text = "\n".join(examples)

            result_text = f"""
✅ <b>Тест успешен!</b>

<b>Источник:</b> {source['name']}
<b>Найдено новостей:</b> {len(news_items)}

<b>Примеры заголовков:</b>
{examples_text}

<b>Статус:</b> Источник работает корректно
            """
        else:
            result_text = f"""
⚠️ <b>Источник доступен, но новостей не найдено</b>

<b>Источник:</b> {source['name']}
<b>Возможные причины:</b>
• RSS лента пуста
• Формат ленты не поддерживается
• Новости старше 24 часов

<b>Рекомендация:</b> Проверьте URL или попробуйте другой источник
            """

        # Возвращаемся к деталям источника
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К источнику", callback_data=f"source_{source_id}")],
                [InlineKeyboardButton(text="📋 К списку", callback_data="list_sources")]
            ]
        )

        await callback.message.edit_text(
            result_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка тестирования источника: {str(e)}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка тестирования</b>\n\n"
            f"Не удалось протестировать источник: {str(e)}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"source_{source_id}")]
                ]
            )
        )


@router.callback_query(F.data == "refresh_sources")
async def refresh_sources(callback: CallbackQuery, db: DatabaseModels):
    """Обновление всех источников"""
    try:
        await callback.message.edit_text(
            "🔄 <b>Обновление источников...</b>\n\n"
            "Проверяю все RSS ленты и получаю свежие новости...",
            parse_mode="HTML"
        )

        sources = await db.get_news_sources()
        total_news = 0
        updated_sources = 0

        async with NewsParser() as parser:
            all_news = await parser.get_news_from_sources(sources)
            total_news = len(all_news)
            updated_sources = len([src for src in sources if src['is_active']])

        await callback.message.edit_text(
            f"✅ <b>Обновление завершено!</b>\n\n"
            f"<b>Обновлено источников:</b> {updated_sources}\n"
            f"<b>Получено новостей:</b> {total_news}\n\n"
            f"Новости готовы к обработке и публикации.",
            parse_mode="HTML",
            reply_markup=news_sources_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка обновления источников: {str(e)}")
        await callback.message.edit_text(
            "❌ <b>Ошибка обновления</b>\n\n"
            "Не удалось обновить источники новостей.",
            parse_mode="HTML",
            reply_markup=news_sources_keyboard()
        )


@router.callback_query(F.data == "back_to_sources")
async def back_to_sources(callback: CallbackQuery):
    """Возврат к управлению источниками"""
    await callback.message.edit_text(
        "📰 <b>Управление источниками новостей</b>\n\n"
        "Здесь вы можете добавлять и настраивать источники новостей для автоматического парсинга.\n\n"
        "Поддерживаются RSS ленты новостных сайтов.",
        parse_mode="HTML",
        reply_markup=news_sources_keyboard()
    )