"""
Модуль для определения возраста фортепиано по серийному номеру
"""

import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from loguru import logger
from age_database import AgeDatabase


@dataclass
class AgeResult:
    """Результат определения возраста"""
    found: bool
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
    """
    Определение возраста фортепиано
    Использует отдельную базу данных piano_age.db
    """

    def __init__(self, db: AgeDatabase):
        self.db = db
        logger.info("AgeDetector инициализирован")

    @staticmethod
    def extract_numbers(text: str) -> Optional[int]:
        """Извлечение чисел из строки"""
        numbers = re.findall(r'\d+', text)
        if not numbers:
            return None
        return int(numbers[0])

    @staticmethod
    def clean_serial(serial: str) -> str:
        """Очистка серийного номера от лишних символов"""
        return re.sub(r'[^0-9a-zA-Z]', '', serial.strip())

    async def find_brand(self, brand_name: str, brand_type: Optional[str] = None) -> Optional[Dict]:
        """
        Поиск бренда в БД с регистронезависимым поиском
        """
        logger.info(f"🔍 Поиск бренда: '{brand_name}', тип: {brand_type}")

        # Пробуем найти точное совпадение (регистронезависимо)
        all_brands = await self.db.get_all_brands(brand_type)

        # Ищем точное совпадение (игнорируя регистр)
        for brand in all_brands:
            if brand['name'].lower() == brand_name.lower():
                logger.info(f"✅ Найден бренд: {brand['name']}")
                return brand

        # Ищем частичное совпадение
        for brand in all_brands:
            if brand_name.lower() in brand['name'].lower() or brand['name'].lower() in brand_name.lower():
                logger.info(f"✅ Найден бренд по частичному совпадению: {brand['name']}")
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

        Args:
            brand_name: Название бренда
            serial_number: Серийный номер
            brand_type: 'foreign' или 'russian'

        Returns:
            AgeResult: Результат определения
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

            # Извлекаем число из серийного номера
            serial_num = self.extract_numbers(serial_clean)
            if serial_num is None:
                return AgeResult(
                    found=False,
                    error="invalid_serial",
                    message=f"Не удалось распознать серийный номер '{serial_number}'. Пожалуйста, введите номер в цифровом формате."
                )

            # Ищем бренд (регистронезависимо)
            brand = await self.find_brand(brand_name, brand_type)
            if not brand:
                # Показываем доступные бренды
                brands_list = await self.get_available_brands(brand_type)
                brands_text = "\n".join([f"• {b}" for b in brands_list])

                return AgeResult(
                    found=False,
                    error="brand_not_found",
                    message=f"Бренд '{brand_name}' не найден в базе.\n\n💡 Проверьте написание или попробуйте ввести бренд на языке оригинала.\n\nДоступные бренды:\n{brands_text}"
                )

            # Ищем серийный номер
            range_data = await self.db.find_age_by_serial(brand['id'], serial_num)
            if not range_data:
                return AgeResult(
                    found=False,
                    error="serial_not_found",
                    message=f"Серийный номер {serial_clean} для бренда '{brand['name']}' не найден.\n\nВозможные причины:\n• Проверьте правильность ввода\n• Номер может быть на другой части инструмента\n• Возможно, номер относится к другой модели\n\n📞 Рекомендуем обратиться к мастеру для точной диагностики."
                )

            # Успешный результат
            return AgeResult(
                found=True,
                brand=brand['name'],
                country=brand['country'],
                info=brand['info'],
                serial=serial_clean,
                year=range_data['year'],
                model=range_data.get('model'),
                brand_type=brand['type']
            )

        except Exception as e:
            logger.error(f"Ошибка определения возраста: {e}")
            return AgeResult(
                found=False,
                error="database_error",
                message="База данных временно недоступна. Пожалуйста, попробуйте позже или обратитесь к администратору."
            )

    async def get_stats(self) -> Dict:
        """Получение статистики по базе данных"""
        brands_count = await self.db.get_brand_count()
        ranges_count = await self.db.get_ranges_count()
        foreign_count = await self.db.get_brand_count('foreign')
        russian_count = await self.db.get_brand_count('russian')

        return {
            "total_brands": brands_count,
            "total_ranges": ranges_count,
            "foreign_brands": foreign_count,
            "russian_brands": russian_count
        }