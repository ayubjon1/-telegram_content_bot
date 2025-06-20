import aiosqlite
from datetime import datetime
from typing import List, Optional, Dict


class DatabaseModels:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица каналов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT UNIQUE NOT NULL,
                    channel_name TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    posts_per_day INTEGER DEFAULT 5,
                    last_post_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица источников новостей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS news_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    source_type TEXT DEFAULT 'rss',
                    is_active BOOLEAN DEFAULT 1,
                    category TEXT DEFAULT 'общее',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица настроек
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

    async def add_channel(self, channel_id: str, channel_name: str, posts_per_day: int = 5):
        """Добавить канал"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO channels (channel_id, channel_name, posts_per_day) VALUES (?, ?, ?)",
                (channel_id, channel_name, posts_per_day)
            )
            await db.commit()

    async def get_channels(self) -> List[Dict]:
        """Получить все каналы"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT channel_id, channel_name, is_active, posts_per_day FROM channels"
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "channel_id": row[0],
                        "channel_name": row[1],
                        "is_active": bool(row[2]),
                        "posts_per_day": row[3]
                    }
                    for row in rows
                ]

    async def add_news_source(self, name: str, url: str, source_type: str = 'rss', category: str = 'общее'):
        """Добавить источник новостей"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO news_sources (name, url, source_type, category) VALUES (?, ?, ?, ?)",
                (name, url, source_type, category)
            )
            await db.commit()

    async def get_news_sources(self) -> List[Dict]:
        """Получить все источники новостей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT id, name, url, source_type, is_active, category FROM news_sources WHERE is_active = 1"
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "url": row[2],
                        "source_type": row[3],
                        "is_active": bool(row[4]),
                        "category": row[5]
                    }
                    for row in rows
                ]

    async def get_setting(self, key: str) -> Optional[str]:
        """Получить настройку"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT value FROM settings WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_setting(self, key: str, value: str):
        """Установить настройку"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat())
            )
            await db.commit()

    async def get_statistics(self, channel_id: str = None) -> Dict:
        """Получить статистику"""
        # Простая заглушка
        return {
            "posts_count": 0,
            "total_views": 0
        }

    async def delete_channel(self, channel_id: str):
        """Удалить канал"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
            await db.commit()

    async def update_channel_status(self, channel_id: str, is_active: bool):
        """Обновить статус канала"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE channels SET is_active = ? WHERE channel_id = ?",
                (is_active, channel_id)
            )
            await db.commit()

    async def get_channel_by_id(self, channel_id: str) -> Optional[Dict]:
        """Получить канал по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT channel_id, channel_name, is_active, posts_per_day FROM channels WHERE channel_id = ?",
                (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "channel_id": row[0],
                        "channel_name": row[1],
                        "is_active": bool(row[2]),
                        "posts_per_day": row[3]
                    }
                return None

    async def update_source_status(self, source_id: int, is_active: bool):
        """Обновить статус источника"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE news_sources SET is_active = ? WHERE id = ?",
                (is_active, source_id)
            )
            await db.commit()

    async def delete_source(self, source_id: int):
        """Удалить источник"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM news_sources WHERE id = ?", (source_id,))
            await db.commit()

    async def get_source_by_id(self, source_id: int) -> Optional[Dict]:
        """Получить источник по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, name, url, source_type, is_active, category FROM news_sources WHERE id = ?",
                (source_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "url": row[2],
                        "source_type": row[3],
                        "is_active": bool(row[4]),
                        "category": row[5]
                    }
                return None

    async def get_all_settings(self) -> Dict[str, str]:
        """Получить все настройки"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT key, value FROM settings") as cursor:
                rows = await cursor.fetchall()
                return {row[0]: row[1] for row in rows}

    async def delete_setting(self, key: str):
        """Удалить настройку"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM settings WHERE key = ?", (key,))
            await db.commit()

    async def update_channel_posts_per_day(self, channel_id: str, posts_per_day: int):
        """Обновить количество постов в день для канала"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE channels SET posts_per_day = ? WHERE channel_id = ?",
                (posts_per_day, channel_id)
            )
            await db.commit()

    async def update_last_post_time(self, channel_id: str):
        """Обновить время последнего поста"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE channels SET last_post_time = ? WHERE channel_id = ?",
                (datetime.now().isoformat(), channel_id)
            )
            await db.commit()

    async def get_active_channels(self) -> List[Dict]:
        """Получить только активные каналы"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT channel_id, channel_name, posts_per_day FROM channels WHERE is_active = 1"
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "channel_id": row[0],
                        "channel_name": row[1],
                        "posts_per_day": row[2]
                    }
                    for row in rows
                ]

    async def get_active_sources(self) -> List[Dict]:
        """Получить только активные источники"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, name, url, category FROM news_sources WHERE is_active = 1"
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "url": row[2],
                        "category": row[3]
                    }
                    for row in rows
                ]