from typing import Union, Optional
import re


class Validators:
    """Валидаторы для вводимых данных"""

    @staticmethod
    def validate_diameter(value: str) -> Optional[float]:
        """Проверка валидности диаметра"""
        try:
            val = float(value.replace(",", "."))
            if 0.1 <= val <= 10.0:
                return round(val, 3)
            return None
        except ValueError:
            return None

    @staticmethod
    def validate_length(value: str) -> Optional[float]:
        """Проверка валидности длины"""
        try:
            val = float(value.replace(",", "."))
            if 100 <= val <= 3000:
                return int(val)
            return None
        except ValueError:
            return None

    @staticmethod
    def validate_username(value: str) -> bool:
        """Проверка валидности username"""
        pattern = r'^[a-zA-Z0-9_]{3,32}$'
        return bool(re.match(pattern, value))

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Очистка текста от потенциально опасных символов"""
        # Удаляем HTML теги и опасные символы
        import html
        text = html.escape(text)
        # Ограничиваем длину
        return text[:4000]