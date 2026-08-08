import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger
from models import User
from config import config


class Database:
    """Работа с базой данных"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db_sync()

    def _init_db_sync(self):
        """Синхронная инициализация таблиц"""
        import asyncio
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self._create_tables())
        except RuntimeError:
            asyncio.run(self._create_tables())

    async def _create_tables(self):
        """Создание или обновление таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, есть ли таблица users
            async with db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            ) as cursor:
                table_exists = await cursor.fetchone()

            if table_exists:
                # Проверяем, есть ли столбец is_super_admin
                async with db.execute("PRAGMA table_info(users)") as cursor:
                    columns = await cursor.fetchall()
                    column_names = [col[1] for col in columns]

                if 'is_super_admin' not in column_names:
                    await db.execute("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT 0")
                    logger.info("✅ Добавлен столбец is_super_admin")

                if 'subscribed_at' not in column_names:
                    await db.execute("ALTER TABLE users ADD COLUMN subscribed_at TIMESTAMP")
                    logger.info("✅ Добавлен столбец subscribed_at")

                await db.commit()
                logger.info("✅ База данных обновлена")
            else:
                # Создаем таблицу с нуля
                await db.execute("""
                    CREATE TABLE users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT NOT NULL,
                        last_name TEXT,
                        is_subscribed BOOLEAN DEFAULT 0,
                        is_admin BOOLEAN DEFAULT 0,
                        is_super_admin BOOLEAN DEFAULT 0,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        subscribed_at TIMESTAMP
                    )
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS calculations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        winding_type INTEGER,
                        core_diameter REAL,
                        total_diameter REAL,
                        length REAL,
                        primary_diam REAL,
                        secondary_diam REAL,
                        primary_length REAL,
                        secondary_length REAL,
                        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)

                await db.commit()
                logger.info("✅ База данных создана")

            # Создаем новые таблицы для определения возраста
            await self._create_age_tables(db)

            # Добавляем супер-админа в БД
            await self._init_super_admin()

    async def _create_age_tables(self, db):
        """Создание таблиц для определения возраста"""
        # Таблица брендов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
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

        await db.commit()
        logger.info("✅ Таблицы для определения возраста созданы")

    async def _init_super_admin(self):
        """Добавление супер-админа в БД"""
        if config.super_admin:
            existing = await self.get_user(config.super_admin)
            if not existing:
                user_data = {
                    'user_id': config.super_admin,
                    'username': 'super_admin',
                    'first_name': 'Super Admin',
                    'last_name': None,
                    'is_subscribed': True,
                    'is_admin': True,
                    'is_super_admin': True
                }
                await self.add_user(user_data)
                logger.info(f"👑 Супер-админ {config.super_admin} добавлен в БД")
            else:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        UPDATE users 
                        SET is_super_admin = 1, is_admin = 1, is_subscribed = 1
                        WHERE user_id = ?
                    """, (config.super_admin,))
                    await db.commit()
                    logger.info(f"👑 Супер-админ {config.super_admin} обновлен в БД")

    # ============ МЕТОДЫ ДЛЯ БРЕНДОВ ============

    async def add_brand(self, name: str, country: str, info: str, brand_type: str = 'foreign') -> int:
        """Добавление нового бренда"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO brands (name, country, info, type)
                VALUES (?, ?, ?, ?)
            """, (name, country, info, brand_type))
            await db.commit()
            return cursor.lastrowid

    async def get_brand_by_name(self, name: str, brand_type: Optional[str] = None) -> Optional[Dict]:
        """Поиск бренда по названию"""
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

    async def search_brands(self, query: str, brand_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Поиск брендов по частичному совпадению"""
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

    async def get_all_brands(self, brand_type: Optional[str] = None) -> List[Dict]:
        """Получение всех брендов"""
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

    async def add_serial_range(self, brand_id: int, serial_start: int, serial_end: int, year: int,
                               model: Optional[str] = None, info: Optional[str] = None) -> int:
        """Добавление диапазона серийных номеров"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO serial_ranges 
                (brand_id, serial_start, serial_end, year, model, info)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (brand_id, serial_start, serial_end, year, model, info))
            await db.commit()
            return cursor.lastrowid

    async def find_age_by_serial(self, brand_id: int, serial_number: int) -> Optional[Dict]:
        """Поиск года выпуска по серийному номеру"""
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

    async def get_brand_with_ranges(self, brand_id: int) -> Optional[Dict]:
        """Получение бренда со всеми диапазонами"""
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

    async def clear_brands_data(self) -> None:
        """Очистка данных о брендах (для переимпорта)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM serial_ranges")
            await db.execute("DELETE FROM brands")
            await db.commit()
            logger.info("🗑️ Данные о брендах очищены")

    # ============ СУЩЕСТВУЮЩИЕ МЕТОДЫ ============

    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def add_user(self, user_data: dict) -> User:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, is_subscribed, is_admin, is_super_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data['user_id'],
                user_data.get('username'),
                user_data['first_name'],
                user_data.get('last_name'),
                user_data.get('is_subscribed', False),
                user_data.get('is_admin', False),
                user_data.get('is_super_admin', False)
            ))
            await db.commit()
            return await self.get_user(user_data['user_id'])

    async def get_user(self, user_id: int) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    row_dict = dict(row)
                    return User(
                        user_id=row_dict['user_id'],
                        username=row_dict['username'],
                        first_name=row_dict['first_name'],
                        last_name=row_dict['last_name'],
                        is_subscribed=bool(row_dict['is_subscribed']),
                        is_admin=bool(row_dict['is_admin']),
                        is_super_admin=bool(row_dict.get('is_super_admin', False)),
                        joined_at=datetime.fromisoformat(row_dict['joined_at']) if row_dict.get('joined_at') else None,
                        subscribed_at=datetime.fromisoformat(row_dict['subscribed_at']) if row_dict.get(
                            'subscribed_at') else None
                    )
                return None

    async def get_subscribed_users(self) -> List[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            users = []
            async with db.execute(
                    "SELECT * FROM users WHERE is_subscribed = 1"
            ) as cursor:
                async for row in cursor:
                    row_dict = dict(row)
                    users.append(User(
                        user_id=row_dict['user_id'],
                        username=row_dict['username'],
                        first_name=row_dict['first_name'],
                        last_name=row_dict['last_name'],
                        is_subscribed=True,
                        is_admin=bool(row_dict['is_admin']),
                        is_super_admin=bool(row_dict.get('is_super_admin', False)),
                        joined_at=datetime.fromisoformat(row_dict['joined_at']) if row_dict.get('joined_at') else None,
                        subscribed_at=datetime.fromisoformat(row_dict['subscribed_at']) if row_dict.get(
                            'subscribed_at') else None
                    ))
            return users

    async def toggle_subscription(self, user_id: int, subscribe: bool) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET is_subscribed = ?, subscribed_at = ?
                WHERE user_id = ?
            """, (
                subscribe,
                datetime.now().isoformat() if subscribe else None,
                user_id
            ))
            await db.commit()
            return True

    async def save_calculation(self, calc_data: dict) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO calculations 
                (user_id, winding_type, core_diameter, total_diameter, length,
                 primary_diam, secondary_diam, primary_length, secondary_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                calc_data['user_id'],
                calc_data['winding_type'],
                calc_data['core_diameter'],
                calc_data['total_diameter'],
                calc_data['length'],
                calc_data['primary_diam'],
                calc_data.get('secondary_diam'),
                calc_data['primary_length'],
                calc_data.get('secondary_length')
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_statistics(self) -> Dict[str, int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total = (await cursor.fetchone())[0]

            async with db.execute(
                    "SELECT COUNT(*) FROM users WHERE is_subscribed = 1"
            ) as cursor:
                subscribed = (await cursor.fetchone())[0]

            async with db.execute(
                    "SELECT COUNT(*) FROM calculations"
            ) as cursor:
                calculations = (await cursor.fetchone())[0]

            today = datetime.now().date()
            async with db.execute(
                    "SELECT COUNT(DISTINCT user_id) FROM calculations WHERE DATE(calculated_at) = ?",
                    (today.isoformat(),)
            ) as cursor:
                active_today = (await cursor.fetchone())[0]

            return {
                "total_users": total,
                "subscribed_users": subscribed,
                "total_calculations": calculations,
                "active_today": active_today
            }

    async def is_user_allowed(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if not user:
            return False
        return user.is_super_admin or user.is_admin or user.is_subscribed

    async def is_admin(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if not user:
            return False
        return user.is_super_admin or user.is_admin

    async def is_super_admin(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if not user:
            return False
        return user.is_super_admin

    async def get_all_users(self) -> List[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            users = []
            async with db.execute(
                    "SELECT * FROM users ORDER BY is_super_admin DESC, is_admin DESC, is_subscribed DESC, joined_at DESC"
            ) as cursor:
                async for row in cursor:
                    row_dict = dict(row)
                    users.append(User(
                        user_id=row_dict['user_id'],
                        username=row_dict['username'],
                        first_name=row_dict['first_name'],
                        last_name=row_dict['last_name'],
                        is_subscribed=bool(row_dict['is_subscribed']),
                        is_admin=bool(row_dict['is_admin']),
                        is_super_admin=bool(row_dict.get('is_super_admin', False)),
                        joined_at=datetime.fromisoformat(row_dict['joined_at']) if row_dict.get('joined_at') else None,
                        subscribed_at=datetime.fromisoformat(row_dict['subscribed_at']) if row_dict.get(
                            'subscribed_at') else None
                    ))
            return users

    async def is_admin_in_env(self, user_id: int) -> bool:
        return user_id in config.admin_ids

    async def is_super_admin_in_env(self, user_id: int) -> bool:
        return user_id == config.super_admin