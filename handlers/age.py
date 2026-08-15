"""
Обработчик определения возраста инструмента
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from age_detector import AgeDetector, AgeResult
from age_database import AgeDatabase
from keyboard.menus import MenuBuilder

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

        total_brands = await self.age_db.get_brand_count()

        if total_brands == 0:
            await query.edit_message_text(
                "❌ База данных брендов пока пуста.",
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
            "🔍 Определение возраста инструмента\n\nВыберите тип инструмента:",
            reply_markup=reply_markup
        )
        return SELECT_TYPE

    async def select_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбор типа инструмента"""
        query = update.callback_query
        await query.answer()

        if query.data == "age_foreign":
            brand_type = "foreign"
            type_name = "иностранных"
        else:
            brand_type = "russian"
            type_name = "отечественных"

        context.user_data['brand_type'] = brand_type
        context.user_data['type_name'] = type_name

        brands = await self.age_db.get_all_brands(brand_type)
        if not brands:
            await query.edit_message_text(
                f"❌ В базе нет {type_name} брендов.",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return SELECT_TYPE

        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="age_back_to_type")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🏷️ Введите название бренда ({type_name} инструментов):",
            reply_markup=reply_markup
        )
        return BRAND_INPUT

    async def get_brand(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение названия бренда"""
        brand_name = update.message.text.strip()

        if not brand_name:
            await update.message.reply_text(
                "❌ Введите название бренда:",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return BRAND_INPUT

        context.user_data['brand_name'] = brand_name

        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="age_back_to_brand")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🔢 Введите серийный номер:\n\nБренд: {brand_name}",
            reply_markup=reply_markup
        )
        return SERIAL_INPUT

    async def get_serial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение серийного номера и выполнение поиска"""
        serial = update.message.text.strip()

        if not serial:
            await update.message.reply_text(
                "❌ Введите серийный номер:",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return SERIAL_INPUT

        brand_name = context.user_data.get('brand_name', '')
        brand_type = context.user_data.get('brand_type', 'foreign')

        try:
            result = await self.detector.detect(brand_name, serial, brand_type)
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            await update.message.reply_text(
                "❌ Ошибка. Попробуйте снова.",
                reply_markup=MenuBuilder.get_back_menu()
            )
            context.user_data.clear()
            return ConversationHandler.END

        if not result or not isinstance(result, AgeResult):
            await update.message.reply_text(
                "❌ Ошибка. Попробуйте снова.",
                reply_markup=MenuBuilder.get_back_menu()
            )
            context.user_data.clear()
            return ConversationHandler.END

        if result.found:
            result_text = (
                "🎹 РЕЗУЛЬТАТ\n"
                "═══════════════\n\n"
                f"🏷️ Бренд: {result.brand or brand_name}\n"
                f"🔢 Серийный номер: {result.serial or serial}\n"
                f"📅 Год выпуска: {result.year if result.year else 'Не определён'}\n"
            )

            if result.country:
                result_text += f"\n🌍 Страна: {result.country}"
            if result.info:
                result_text += f"\n📌 Информация: {result.info}"

            keyboard = [
                [InlineKeyboardButton("🔄 Новый поиск", callback_data="age_start")],
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(result_text, reply_markup=reply_markup)
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="age_start")],
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            error_message = result.message if result.message else "Ошибка."
            await update.message.reply_text(f"❌ {error_message}", reply_markup=reply_markup)

        context.user_data.clear()
        return ConversationHandler.END

    # ==================== КНОПКИ НАЗАД ====================

    async def back_to_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        context.user_data.clear()

        total_brands = await self.age_db.get_brand_count()
        if total_brands == 0:
            await query.edit_message_text(
                "❌ База данных пуста.",
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
            "🔍 Определение возраста\n\nВыберите тип:",
            reply_markup=reply_markup
        )
        return SELECT_TYPE

    async def back_to_brand(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        context.user_data.pop('brand_name', None)

        type_name = context.user_data.get('type_name', '')

        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="age_back_to_type")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🏷️ Введите бренд ({type_name}):",
            reply_markup=reply_markup
        )
        return BRAND_INPUT

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        context.user_data.clear()

        await query.edit_message_text(
            "🔍 Поиск отменен.",
            reply_markup=MenuBuilder.get_back_menu()
        )
        return ConversationHandler.END