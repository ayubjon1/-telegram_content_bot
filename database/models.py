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
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
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