"""
Обработчик определения возраста инструмента
Использует piano_age.db
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from age_detector import AgeDetector
from age_database import AgeDatabase
from keyboard.menus import MenuBuilder

# Состояния для ConversationHandler
SELECT_TYPE, BRAND_INPUT, SERIAL_INPUT = range(3)


class AgeHandler:
    """Обработчик определения возраста инструмента"""

    def __init__(self, age_db: AgeDatabase):
        self.age_db = age_db
        self.detector = AgeDetector(age_db)
        logger.info("AgeHandler инициализирован")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск определения возраста"""
        query = update.callback_query
        await query.answer()

        # Проверяем наличие брендов в базе
        total_brands = await self.age_db.get_brand_count()
        logger.info(f"📊 Всего брендов в базе: {total_brands}")

        if total_brands == 0:
            await query.edit_message_text(
                "❌ База данных брендов пока пуста.\n\n"
                "Пожалуйста, обратитесь к администратору для загрузки данных.",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return ConversationHandler.END

        # Показываем выбор типа
        keyboard = [
            [InlineKeyboardButton("🇪🇺 Иностранные", callback_data="age_foreign")],
            [InlineKeyboardButton("🇷🇺 Отечественные", callback_data="age_russian")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🔍 Определение возраста инструмента\n\n"
            "Выберите тип инструмента:",
            reply_markup=reply_markup
        )
        return SELECT_TYPE

    async def select_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбор типа инструмента"""
        query = update.callback_query
        await query.answer()

        # Сохраняем тип
        if query.data == "age_foreign":
            brand_type = "foreign"
            type_name = "иностранных"
        else:
            brand_type = "russian"
            type_name = "отечественных"

        context.user_data['brand_type'] = brand_type
        context.user_data['type_name'] = type_name

        # Проверяем, есть ли бренды такого типа
        brands = await self.age_db.get_all_brands(brand_type)
        if not brands:
            await query.edit_message_text(
                f"❌ В базе данных пока нет {type_name} брендов.\n\n"
                f"База данных {type_name} будет добавлена позже.\n"
                f"Пожалуйста, выберите другой тип.",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return SELECT_TYPE

        # Показываем поле для ввода бренда
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="age_back_to_type")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🏷️ Введите название бренда ({type_name} инструментов):\n\n"
            f"(например: Steinway, Yamaha, Красный Октябрь, Аккорд)",
            reply_markup=reply_markup
        )
        return BRAND_INPUT

    async def get_brand(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение названия бренда"""
        brand_name = update.message.text.strip()

        if not brand_name:
            await update.message.reply_text(
                "❌ Пожалуйста, введите название бренда:",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return BRAND_INPUT

        context.user_data['brand_name'] = brand_name

        # Показываем поле для ввода серийного номера
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="age_back_to_brand")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🔢 Введите серийный номер инструмента:\n\n"
            f"Бренд: {brand_name}\n"
            f"(указан на чугунной раме или за верхней декой)",
            reply_markup=reply_markup
        )
        return SERIAL_INPUT

    async def get_serial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение серийного номера и выполнение поиска"""
        serial = update.message.text.strip()

        if not serial:
            await update.message.reply_text(
                "❌ Пожалуйста, введите серийный номер:",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return SERIAL_INPUT

        # Получаем данные из контекста
        brand_name = context.user_data.get('brand_name', '')
        brand_type = context.user_data.get('brand_type', 'foreign')

        # Выполняем поиск
        result = await self.detector.detect(brand_name, serial, brand_type)

        if result.found:
            # Успешный результат
            result_text = (
                "🎹 РЕЗУЛЬТАТ ОПРЕДЕЛЕНИЯ ВОЗРАСТА\n"
                "═══════════════════════════════════\n\n"
                f"🏷️ Бренд: {result.brand}\n"
                f"🔢 Серийный номер: {result.serial}\n"
                f"📅 Год выпуска: {result.year}\n"
            )

            if result.country:
                result_text += f"\n🌍 Страна: {result.country}"

            if result.info:
                result_text += f"\n📌 Информация: {result.info}"

            if result.model:
                result_text += f"\n📐 Модель: {result.model}"

            # Кнопки
            keyboard = [
                [InlineKeyboardButton("🔄 Новый поиск", callback_data="age_start")],
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                result_text,
                reply_markup=reply_markup
            )

            # Очищаем контекст
            context.user_data.clear()
            return ConversationHandler.END

        else:
            # Ошибка
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="age_start")],
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"❌ {result.message}",
                reply_markup=reply_markup
            )

            # Очищаем контекст
            context.user_data.clear()
            return ConversationHandler.END

    # ==================== КНОПКИ НАЗАД ====================

    async def back_to_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат к выбору типа"""
        query = update.callback_query
        await query.answer()
        context.user_data.clear()

        # Проверяем наличие брендов в базе
        total_brands = await self.age_db.get_brand_count()

        if total_brands == 0:
            await query.edit_message_text(
                "❌ База данных брендов пока пуста.\n\n"
                "Пожалуйста, обратитесь к администратору для загрузки данных.",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton("🇪🇺 Иностранные", callback_data="age_foreign")],
            [InlineKeyboardButton("🇷🇺 Отечественные", callback_data="age_russian")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🔍 Определение возраста инструмента\n\n"
            "Выберите тип инструмента:",
            reply_markup=reply_markup
        )
        return SELECT_TYPE

    async def back_to_brand(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат к вводу бренда"""
        query = update.callback_query
        await query.answer()
        context.user_data.pop('brand_name', None)

        type_name = context.user_data.get('type_name', '')

        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="age_back_to_type")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🏷️ Введите название бренда ({type_name} инструментов):\n\n"
            f"(например: Steinway, Yamaha, Красный Октябрь, Аккорд)",
            reply_markup=reply_markup
        )
        return BRAND_INPUT

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена и возврат в главное меню"""
        query = update.callback_query
        await query.answer()
        context.user_data.clear()

        await query.edit_message_text(
            "🔍 Поиск отменен.",
            reply_markup=MenuBuilder.get_back_menu()
        )
        return ConversationHandler.END