"""
База данных для определения возраста инструментов
Отдельный файл piano_age.db
"""

import aiosqlite
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime


class AgeDatabase:
    """Класс для работы с базой данных возраста инструментов"""

    def __init__(self, db_path: str = "piano_age.db"):
        self.db_path = db_path
        self._init_db_sync()
        logger.info(f"✅ AgeDatabase инициализирован: {db_path}")

    def _init_db_sync(self):
        """Синхронная инициализация таблиц"""
        import asyncio
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self._create_tables())
        except RuntimeError:
            asyncio.run(self._create_tables())

    async def _create_tables(self):
        """Создание таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS brands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    country TEXT,
                    info TEXT,
                    type TEXT DEFAULT 'foreign',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS serial_ranges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand_id INTEGER NOT NULL,
                    serial_start INTEGER NOT NULL,
                    serial_end INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    model TEXT,
                    info TEXT,
                    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
                )
            """)

            await db.execute("CREATE INDEX IF NOT EXISTS idx_serial_ranges_brand ON serial_ranges(brand_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_brands_name ON brands(name)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_brands_type ON brands(type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_serial_ranges_serial ON serial_ranges(serial_start, serial_end)")

            await db.commit()
            logger.info("✅ Таблицы созданы в piano_age.db")

    async def add_brand(self, name: str, country: str, info: str, brand_type: str = 'foreign') -> Optional[int]:
        """Добавление бренда"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT id FROM brands WHERE name = ?", (name,)) as cursor:
                    existing = await cursor.fetchone()
                    if existing:
                        return existing[0]

                cursor = await db.execute("""
                    INSERT INTO brands (name, country, info, type)
                    VALUES (?, ?, ?, ?)
                """, (name, country, info, brand_type))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления бренда {name}: {e}")
            return None

    async def get_brand_by_name(self, name: str) -> Optional[Dict]:
        """Поиск бренда по точному названию"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM brands WHERE LOWER(name) = LOWER(?)", (name,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка поиска бренда: {e}")
            return None

    async def get_all_brands(self, brand_type: Optional[str] = None) -> List[Dict]:
        """Получение всех брендов"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                query = "SELECT * FROM brands"
                params = []

                if brand_type:
                    query += " WHERE type = ?"
                    params.append(brand_type)

                query += " ORDER BY name"

                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения брендов: {e}")
            return []

    async def get_brand_count(self, brand_type: Optional[str] = None) -> int:
        """Количество брендов"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = "SELECT COUNT(*) FROM brands"
                params = []

                if brand_type:
                    query += " WHERE type = ?"
                    params.append(brand_type)

                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else 0
        except Exception as e:
            logger.error(f"Ошибка получения количества брендов: {e}")
            return 0

    async def add_serial_range(self, brand_id: int, serial_start: int, serial_end: int,
                                year: int, model: Optional[str] = None,
                                info: Optional[str] = None) -> Optional[int]:
        """Добавление диапазона серийных номеров"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO serial_ranges 
                    (brand_id, serial_start, serial_end, year, model, info)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (brand_id, serial_start, serial_end, year, model, info))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления диапазона: {e}")
            return None

    async def find_age_by_serial(self, brand_id: int, serial_number: int) -> Optional[Dict]:
        """
        Поиск года выпуска по серийному номеру
        Использует BETWEEN для точного поиска
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT sr.year, sr.serial_start, sr.serial_end, sr.model, sr.info,
                           b.name as brand_name, b.country, b.info as brand_info
                    FROM serial_ranges sr
                    JOIN brands b ON sr.brand_id = b.id
                    WHERE sr.brand_id = ? AND ? BETWEEN sr.serial_start AND sr.serial_end
                    LIMIT 1
                """, (brand_id, serial_number)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        result = dict(row)
                        logger.info(f"✅ Найден год: {result['year']} для номера {serial_number}")
                        return result
                    logger.warning(f"❌ Номер {serial_number} не найден для бренда {brand_id}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка поиска серийного номера: {e}")
            return None

    async def get_ranges_count(self) -> int:
        """Количество диапазонов"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT COUNT(*) FROM serial_ranges") as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else 0
        except Exception as e:
            logger.error(f"Ошибка получения количества диапазонов: {e}")
            return 0

    async def clear_all_data(self) -> None:
        """Очистка всех данных"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM serial_ranges")
                await db.execute("DELETE FROM brands")
                await db.commit()
                logger.info("🗑️ Все данные в piano_age.db очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")