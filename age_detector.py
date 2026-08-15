"""
Модуль для определения возраста фортепиано по серийному номеру
"""

import re
import unicodedata
from typing import Optional, Dict, List
from dataclasses import dataclass
from loguru import logger
from age_database import AgeDatabase


@dataclass
class AgeResult:
    """Результат определения возраста"""
    found: bool = False
    brand: Optional[str] = None
    country: Optional[str] = None
    info: Optional[str] = None
    serial: Optional[str] = None
    year: Optional[int] = None
    model: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None
    brand_type: Optional[str] = None


class AgeDetector:
    """Определение возраста фортепиано"""

    def __init__(self, db: AgeDatabase):
        self.db = db
        logger.info("AgeDetector инициализирован")

    @staticmethod
    def normalize_string(text: str) -> str:
        """
        Нормализация строки: удаление диакритических знаков и приведение к нижнему регистру
        """
        text = text.lower()
        normalized = unicodedata.normalize('NFKD', text)
        without_diacritics = ''.join(c for c in normalized if not unicodedata.combining(c))
        return without_diacritics

    @staticmethod
    def extract_numbers(text: str) -> Optional[int]:
        """Извлечение чисел из строки"""
        numbers = re.findall(r'\d+', text)
        if not numbers:
            return None
        return int(numbers[0])

    @staticmethod
    def clean_serial(serial: str) -> str:
        """Очистка серийного номера"""
        return re.sub(r'[^0-9a-zA-Z]', '', serial.strip())

    async def find_brand(self, brand_name: str, brand_type: Optional[str] = None) -> Optional[Dict]:
        """
        Поиск бренда с нормализацией
        """
        logger.info(f"🔍 Поиск бренда: '{brand_name}'")

        normalized_input = self.normalize_string(brand_name)
        logger.info(f"📝 Нормализованный ввод: '{normalized_input}'")

        all_brands = await self.db.get_all_brands(brand_type)
        logger.info(f"📋 Всего брендов в базе: {len(all_brands)}")

        # 1. Точное совпадение (нормализованное)
        for brand in all_brands:
            brand_normalized = self.normalize_string(brand['name'])
            if brand_normalized == normalized_input:
                logger.info(f"✅ Найден бренд: {brand['name']}")
                return brand

        # 2. Частичное совпадение
        for brand in all_brands:
            brand_normalized = self.normalize_string(brand['name'])
            if normalized_input in brand_normalized or brand_normalized in normalized_input:
                logger.info(f"✅ Найден по частичному: {brand['name']}")
                return brand

        logger.warning(f"❌ Бренд не найден: {brand_name}")
        return None

    async def get_available_brands(self, brand_type: str = 'foreign', limit: int = 10) -> List[str]:
        """Получение списка доступных брендов"""
        brands = await self.db.get_all_brands(brand_type)
        return [f"{b['name']} ({b['country']})" for b in brands[:limit]]

    async def detect(self, brand_name: str, serial_number: str, brand_type: str = 'foreign') -> AgeResult:
        """
        Основной метод определения возраста
        """
        try:
            # Очищаем серийный номер
            serial_clean = self.clean_serial(serial_number)
            if not serial_clean:
                return AgeResult(
                    found=False,
                    error="invalid_serial",
                    message="Не удалось распознать серийный номер."
                )

            # Извлекаем число
            serial_num = self.extract_numbers(serial_clean)
            if serial_num is None:
                return AgeResult(
                    found=False,
                    error="invalid_serial",
                    message=f"Не удалось распознать серийный номер '{serial_number}'. Введите номер в цифровом формате."
                )

            logger.info(f"🔢 Серийный номер: {serial_num}")

            # Ищем бренд
            brand = await self.find_brand(brand_name, brand_type)
            if not brand:
                brands_list = await self.get_available_brands(brand_type)
                brands_text = "\n".join([f"• {b}" for b in brands_list])
                return AgeResult(
                    found=False,
                    error="brand_not_found",
                    message=f"Бренд '{brand_name}' не найден.\n\nДоступные бренды:\n{brands_text}"
                )

            # Ищем серийный номер
            range_data = await self.db.find_age_by_serial(brand['id'], serial_num)

            if not range_data or not isinstance(range_data, dict):
                return AgeResult(
                    found=False,
                    error="serial_not_found",
                    message=f"Серийный номер {serial_clean} для бренда '{brand['name']}' не найден.\n\nПроверьте правильность ввода."
                )

            # Успешный результат
            return AgeResult(
                found=True,
                brand=brand.get('name', brand_name),
                country=brand.get('country', 'Неизвестно'),
                info=brand.get('info', ''),
                serial=serial_clean,
                year=range_data.get('year'),
                model=range_data.get('model'),
                brand_type=brand.get('type', brand_type)
            )

        except Exception as e:
            logger.error(f"Ошибка определения возраста: {e}")
            import traceback
            traceback.print_exc()
            return AgeResult(
                found=False,
                error="database_error",
                message="Произошла ошибка. Попробуйте позже."
            )