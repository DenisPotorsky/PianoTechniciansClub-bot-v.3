"""
Калькулятор для изготовления басовых струн
Формулы из оригинального приложения
"""

import math


class StringCalculator:
    """Калькулятор басовых струн"""

    PI = math.pi

    @staticmethod
    def cooper_diam(general: float, kern: float) -> float:
        """
        Вычисление диаметра меди для одиночной струны
        Formula: (general - kern) / 2
        """
        return (general - kern) / 2

    @staticmethod
    def length_cooper(kern: float, cooper: float, length: float) -> float:
        """
        Вычисление длины меди для одиночной струны
        Formula: (kern + cooper * 2) * pi * length
        """
        return (kern + cooper * 2) * StringCalculator.PI * length

    @staticmethod
    def cooper_first(general: float, kern: float) -> float:
        """
        Вычисление диаметра меди для первичной навивки (33.34%)
        Formula: ((general - kern) * 0.3334) / 2
        """
        return ((general - kern) * 0.3334) / 2

    @staticmethod
    def cooper_second(general: float, kern: float) -> float:
        """
        Вычисление диаметра меди для вторичной навивки (66.67%)
        Formula: ((general - kern) * 0.6667) / 2
        """
        return ((general - kern) * 0.6667) / 2

    @staticmethod
    def length_cooper_primary(kern: float, length: float, cooper_first: float) -> float:
        """
        Вычисление длины меди для первичной навивки
        Formula: (kern + cooper_first * 2) * pi * length - 50
        """
        return (kern + cooper_first * 2) * StringCalculator.PI * length - 50

    @staticmethod
    def length_cooper_secondary(kern: float, length: float, cooper_first: float, cooper_second: float) -> float:
        """
        Вычисление длины меди для вторичной навивки
        Formula: ((kern + (cooper_first * 2)) + (cooper_second * 2)) * pi * length
        """
        return ((kern + (cooper_first * 2)) + (cooper_second * 2)) * StringCalculator.PI * length

    @staticmethod
    def calculate_single_wound(kern: float, general: float, length: float) -> dict:
        """
        Расчет для одиночной навивки
        """
        cooper = StringCalculator.cooper_diam(general, kern)
        cooper_rounded = round(cooper, 3)
        length_cooper = StringCalculator.length_cooper(kern, cooper, length)
        length_cooper_int = int(length_cooper)

        return {
            'copper_diam': cooper_rounded,
            'copper_length': length_cooper_int,
            'type': 'single'
        }

    @staticmethod
    def calculate_double_wound(kern: float, general: float, length: float) -> dict:
        """
        Расчет для двойной навивки
        """
        cooper_first = StringCalculator.cooper_first(general, kern)
        cooper_first_rounded = round(cooper_first, 3)

        cooper_second = StringCalculator.cooper_second(general, kern)
        cooper_second_rounded = round(cooper_second, 3)

        length_primary = StringCalculator.length_cooper_primary(kern, length, cooper_first)
        length_primary_int = int(length_primary)

        length_secondary = StringCalculator.length_cooper_secondary(kern, length, cooper_first, cooper_second)
        length_secondary_int = int(length_secondary)

        return {
            'copper_first_diam': cooper_first_rounded,
            'copper_second_diam': cooper_second_rounded,
            'copper_primary_length': length_primary_int,
            'copper_secondary_length': length_secondary_int,
            'type': 'double'
        }

    @staticmethod
    def calculate(winding_type: int, kern: float, general: float, length: float) -> dict:
        """
        Основной метод расчета

        Args:
            winding_type: 1 - одиночная, 2 - двойная
            kern: диаметр керна
            general: общий диаметр
            length: длина струны

        Returns:
            dict: Результаты расчета
        """
        if winding_type == 1:
            return StringCalculator.calculate_single_wound(kern, general, length)
        else:
            return StringCalculator.calculate_double_wound(kern, general, length)


# Для обратной совместимости с оригинальным кодом
class Calculator:
    """Класс для обратной совместимости с оригинальным кодом"""

    @staticmethod
    def cooperDiam(general, kern):
        return (general - kern) / 2

    @staticmethod
    def lengthCooper(kern, cooper, length):
        return (kern + cooper * 2) * math.pi * length

    @staticmethod
    def cooperFirst(general, kern):
        return ((general - kern) * 0.3334) / 2

    @staticmethod
    def cooperSecond(general, kern):
        return ((general - kern) * 0.6667) / 2

    @staticmethod
    def lengthCooperPrimary(kern, length, cooperFirst):
        return (kern + cooperFirst * 2) * math.pi * length - 50

    @staticmethod
    def lengthCooperSecondary(kern, length, cooperFirst, cooperSecond):
        return ((kern + (cooperFirst * 2)) + (cooperSecond * 2)) * math.pi * length