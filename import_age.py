#!/usr/bin/env python3
"""
Скрипт для импорта данных о брендах в базу данных piano_age.db
Поддерживает импорт иностранных и отечественных брендов
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from age_database import AgeDatabase
from data_russian import RUSSIAN_BRANDS

# Пытаемся импортировать иностранные бренды, если файл существует
try:
    from data_foreign import FOREIGN_BRANDS

    FOREIGN_AVAILABLE = True
except ImportError:
    FOREIGN_AVAILABLE = False
    logger.warning("⚠️ Файл data_foreign.py не найден. Импорт только отечественных брендов.")


class DataImporter:
    """Класс для импорта данных о брендах"""

    def __init__(self, db: AgeDatabase):
        self.db = db
        self.stats = {"brands": 0, "ranges": 0, "errors": 0}

    async def import_brands(self, brands_data: dict, brand_type: str = 'russian') -> dict:
        """Импорт брендов в базу данных"""
        logger.info(f"🚀 Начинаем импорт {brand_type} брендов...")

        total_brands = len(brands_data)
        current = 0

        for brand_name, brand_info in brands_data.items():
            current += 1
            try:
                brand_id = await self.db.add_brand(
                    name=brand_name,
                    country=brand_info.get('country', ''),
                    info=brand_info.get('info', ''),
                    brand_type=brand_info.get('type', brand_type)
                )

                if not brand_id:
                    logger.error(f"❌ Не удалось добавить бренд: {brand_name}")
                    self.stats["errors"] += 1
                    continue

                self.stats["brands"] += 1

                ranges = brand_info.get('ranges', [])
                ranges_count = len(ranges)

                for serial_start, serial_end, year in ranges:
                    await self.db.add_serial_range(
                        brand_id=brand_id,
                        serial_start=serial_start,
                        serial_end=serial_end,
                        year=year
                    )
                    self.stats["ranges"] += 1

                logger.info(f"  [{current}/{total_brands}] ✅ {brand_name} ({ranges_count} диапазонов)")

            except Exception as e:
                logger.error(f"❌ Ошибка импорта бренда {brand_name}: {e}")
                self.stats["errors"] += 1

        return self.stats


async def main():
    """Главная функция"""
    logger.info("=" * 60)
    logger.info("📦 ИМПОРТ ДАННЫХ В piano_age.db")
    logger.info("=" * 60)

    db = AgeDatabase("piano_age.db")
    importer = DataImporter(db)

    # Проверяем, есть ли уже данные
    existing_brands = await db.get_brand_count()

    if existing_brands > 0:
        logger.info(f"⚠️ В базе уже есть {existing_brands} брендов.")
        logger.info("📌 Данные будут добавлены к существующим")

    # Импортируем отечественные бренды
    logger.info("\n🇷🇺 ИМПОРТ ОТЕЧЕСТВЕННЫХ БРЕНДОВ")
    logger.info("=" * 30)
    russian_stats = await importer.import_brands(RUSSIAN_BRANDS, 'russian')

    # Импортируем иностранные бренды (если доступны)
    if FOREIGN_AVAILABLE:
        logger.info("\n🇪🇺 ИМПОРТ ИНОСТРАННЫХ БРЕНДОВ")
        logger.info("=" * 30)
        foreign_stats = await importer.import_brands(FOREIGN_BRANDS, 'foreign')

    # Итоговая статистика
    logger.info("=" * 60)
    logger.info("📊 СТАТИСТИКА ИМПОРТА")
    logger.info(f"   Всего брендов в БД: {await db.get_brand_count()}")
    logger.info(f"   Всего диапазонов в БД: {await db.get_ranges_count()}")

    # Показываем бренды по типам
    foreign_brands = await db.get_all_brands('foreign')
    russian_brands = await db.get_all_brands('russian')
    logger.info(f"\n🇪🇺 Иностранных брендов: {len(foreign_brands)}")
    logger.info(f"🇷🇺 Отечественных брендов: {len(russian_brands)}")

    if len(russian_brands) > 0:
        logger.info("\n📋 Первые 10 отечественных брендов:")
        for brand in russian_brands[:10]:
            logger.info(f"   • {brand['name']} - {brand['country']}")

    logger.info("=" * 60)
    logger.info("✅ Импорт завершен успешно!")


if __name__ == "__main__":
    asyncio.run(main())