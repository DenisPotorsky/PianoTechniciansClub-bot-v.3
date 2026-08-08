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
        # Создаём таблицы синхронно при инициализации
        import asyncio
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self._create_tables())
        except RuntimeError:
            asyncio.run(self._create_tables())
        logger.info(f"✅ AgeDatabase инициализирован: {db_path}")

    async def _create_tables(self):
        """Создание таблиц"""
        logger.info("📦 Создание таблиц в piano_age.db...")
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица брендов
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

            # Таблица диапазонов серийных номеров
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

            # Индексы для быстрого поиска
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_serial_ranges_brand 
                ON serial_ranges(brand_id)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_brands_name 
                ON brands(name)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_brands_type 
                ON brands(type)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_serial_ranges_serial 
                ON serial_ranges(serial_start, serial_end)
            """)

            await db.commit()
            logger.info("✅ Таблицы созданы в piano_age.db")

    # ============ МЕТОДЫ ДЛЯ РАБОТЫ С БРЕНДАМИ ============

    async def add_brand(self, name: str, country: str, info: str, brand_type: str = 'foreign') -> Optional[int]:
        """Добавление бренда"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Проверяем, существует ли уже бренд
                async with db.execute(
                    "SELECT id FROM brands WHERE name = ?", (name,)
                ) as cursor:
                    existing = await cursor.fetchone()
                    if existing:
                        return existing[0]

                # Добавляем новый бренд
                cursor = await db.execute("""
                    INSERT INTO brands (name, country, info, type)
                    VALUES (?, ?, ?, ?)
                """, (name, country, info, brand_type))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления бренда {name}: {e}")
            return None

    async def get_brand_by_name(self, name: str, brand_type: Optional[str] = None) -> Optional[Dict]:
        """Поиск бренда по названию"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                query = "SELECT * FROM brands WHERE LOWER(name) = LOWER(?)"
                params = [name]

                if brand_type:
                    query += " AND type = ?"
                    params.append(brand_type)

                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка поиска бренда: {e}")
            return None

    async def search_brands(self, query: str, brand_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Поиск брендов по частичному совпадению"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                sql_query = """
                    SELECT * FROM brands 
                    WHERE LOWER(name) LIKE LOWER(?)
                """
                params = [f"%{query}%"]

                if brand_type:
                    sql_query += " AND type = ?"
                    params.append(brand_type)

                sql_query += " LIMIT ?"
                params.append(limit)

                async with db.execute(sql_query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка поиска брендов: {e}")
            return []

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

    # ============ МЕТОДЫ ДЛЯ РАБОТЫ С ДИАПАЗОНАМИ ============

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
        """Поиск года выпуска по серийному номеру"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT * FROM serial_ranges 
                    WHERE brand_id = ? AND serial_start <= ? AND serial_end >= ?
                    ORDER BY year ASC
                    LIMIT 1
                """, (brand_id, serial_number, serial_number)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
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

    async def get_brand_with_ranges(self, brand_id: int) -> Optional[Dict]:
        """Получение бренда со всеми диапазонами"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                # Получаем бренд
                async with db.execute("SELECT * FROM brands WHERE id = ?", (brand_id,)) as cursor:
                    brand = await cursor.fetchone()
                    if not brand:
                        return None
                    brand_dict = dict(brand)

                # Получаем диапазоны
                async with db.execute("""
                    SELECT * FROM serial_ranges 
                    WHERE brand_id = ? 
                    ORDER BY serial_start
                """, (brand_id,)) as cursor:
                    ranges = await cursor.fetchall()
                    brand_dict['ranges'] = [dict(row) for row in ranges]

                return brand_dict
        except Exception as e:
            logger.error(f"Ошибка получения бренда с диапазонами: {e}")
            return None

    async def clear_all_data(self) -> None:
        """Очистка всех данных (для переимпорта)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM serial_ranges")
                await db.execute("DELETE FROM brands")
                await db.commit()
                logger.info("🗑️ Все данные в piano_age.db очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")

    async def clear_data_by_type(self, brand_type: str) -> None:
        """Очистка данных по типу (foreign или russian)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Получаем ID брендов указанного типа
                async with db.execute(
                    "SELECT id FROM brands WHERE type = ?", (brand_type,)
                ) as cursor:
                    brand_ids = [row[0] for row in await cursor.fetchall()]

                if brand_ids:
                    # Удаляем диапазоны
                    placeholders = ','.join('?' * len(brand_ids))
                    await db.execute(f"""
                        DELETE FROM serial_ranges 
                        WHERE brand_id IN ({placeholders})
                    """, brand_ids)

                    # Удаляем бренды
                    await db.execute(f"""
                        DELETE FROM brands 
                        WHERE type = ?
                    """, (brand_type,))

                    await db.commit()
                    logger.info(f"🗑️ Данные типа {brand_type} очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки данных по типу: {e}")