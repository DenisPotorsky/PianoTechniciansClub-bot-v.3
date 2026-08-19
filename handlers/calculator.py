"""
Калькулятор басовых струн - обработчик
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from calculator import Calculator
from database import Database
from keyboard.menus import MenuBuilder

# Состояния для ConversationHandler
SELECT_WINDING, CORE_DIAM, TOTAL_DIAM, LENGTH = range(4)


class CalculatorHandler:
    """Обработчик калькулятора"""

    def __init__(self, db: Database):
        self.db = db
        logger.info("CalculatorHandler инициализирован")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /calculator - начало работы калькулятора"""
        logger.info(f"start_command вызван пользователем {update.effective_user.id}")
        user = await self.db.get_user(update.effective_user.id)
        is_admin = user.is_admin or user.is_super_admin if user else False

        # Проверка доступа
        if not user or not (user.is_super_admin or user.is_admin or user.is_subscribed):
            await update.message.reply_text(
                "🔒 *Доступ ограничен*\n\n"
                "Калькулятор доступен только участникам клуба.",
                reply_markup=MenuBuilder.get_main_menu(user, is_admin),
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        # Меню выбора типа навивки
        keyboard = [
            [InlineKeyboardButton("🎵 Одиночная навивка", callback_data="winding_single")],
            [InlineKeyboardButton("🎶 Двойная навивка", callback_data="winding_double")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🧮 *Калькулятор басовых струн*\n\n"
            "Выберите тип навивки:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return SELECT_WINDING

    async def start_calculation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск калькулятора из меню (callback)"""
        query = update.callback_query
        if query is None:
            logger.error("callback_query is None")
            return ConversationHandler.END

        await query.answer()
        logger.info(f"start_calculation вызван пользователем {update.effective_user.id}")

        user = await self.db.get_user(update.effective_user.id)
        is_admin = user.is_admin or user.is_super_admin if user else False

        # Проверка доступа
        if not user or not (user.is_super_admin or user.is_admin or user.is_subscribed):
            await query.edit_message_text(
                "🔒 *Доступ ограничен*\n\n"
                "Калькулятор доступен только участникам клуба.",
                reply_markup=MenuBuilder.get_main_menu(user, is_admin),
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        # Меню выбора типа навивки
        keyboard = [
            [InlineKeyboardButton("🎵 Одиночная навивка", callback_data="winding_single")],
            [InlineKeyboardButton("🎶 Двойная навивка", callback_data="winding_double")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🧮 *Калькулятор басовых струн*\n\n"
            "Выберите тип навивки:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return SELECT_WINDING

    async def select_winding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбор типа навивки"""
        query = update.callback_query
        if query is None:
            logger.error("callback_query is None")
            return ConversationHandler.END

        await query.answer()
        logger.info(f"select_winding вызван. Data: {query.data}")

        # Определяем тип
        if query.data == "winding_single":
            winding_type = 1
            winding_name = "одиночной"
        else:
            winding_type = 2
            winding_name = "двойной"

        # Сохраняем в контекст
        context.user_data['winding_type'] = winding_type
        context.user_data['winding_name'] = winding_name

        logger.info(f"Выбран тип навивки: {winding_type} ({winding_name})")

        # Кнопка назад
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_winding")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🎯 *Настройка {winding_name} навивки*\n\n"
            "📌 *Шаг 1 из 3*\n\n"
            "Введите диаметр керна (в мм):\n"
            "*(например: 0.85)*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return CORE_DIAM

    async def get_core_diameter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение диаметра керна"""
        logger.info(f"get_core_diameter вызван. Текст: '{update.message.text}'")

        try:
            text = update.message.text.replace(",", ".")
            core_diam = float(text)
            logger.info(f"Преобразовано в число: {core_diam}")

            if core_diam <= 0:
                await update.message.reply_text(
                    "❌ Диаметр должен быть положительным числом!\n\n"
                    "Введите диаметр керна (в мм):",
                    reply_markup=MenuBuilder.get_back_menu()
                )
                return CORE_DIAM

            context.user_data['core_diameter'] = core_diam
            logger.info(f"Сохранен диаметр керна: {core_diam}")

            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_core")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ Диаметр керна: {core_diam:.3f} мм\n\n"
                "📌 *Шаг 2 из 3*\n\n"
                "Введите общий диаметр струны (в мм):\n"
                "*(например: 1.25)*\n\n"
                f"⚠️ Должен быть больше {core_diam:.3f} мм",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return TOTAL_DIAM

        except ValueError:
            await update.message.reply_text(
                "❌ Ошибка! Введите корректное число (используйте точку или запятую).\n\n"
                "Введите диаметр керна (в мм):",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return CORE_DIAM

    async def get_total_diameter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение общего диаметра"""
        logger.info(f"get_total_diameter вызван. Текст: '{update.message.text}'")

        try:
            text = update.message.text.replace(",", ".")
            total_diam = float(text)
            logger.info(f"Преобразовано в число: {total_diam}")

            core_diam = context.user_data.get('core_diameter', 0)
            logger.info(f"Диаметр керна из контекста: {core_diam}")

            if total_diam <= core_diam:
                await update.message.reply_text(
                    f"❌ Общий диаметр ({total_diam:.3f} мм) должен быть больше "
                    f"диаметра керна ({core_diam:.3f} мм)!\n\n"
                    "Введите общий диаметр струны (в мм):",
                    reply_markup=MenuBuilder.get_back_menu()
                )
                return TOTAL_DIAM

            context.user_data['total_diameter'] = total_diam
            logger.info(f"Сохранен общий диаметр: {total_diam}")

            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_total")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ Общий диаметр: {total_diam:.3f} мм\n\n"
                "📌 *Шаг 3 из 3*\n\n"
                "Введите длину навивки (в мм):\n"
                "*(например: 950)*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return LENGTH

        except ValueError:
            await update.message.reply_text(
                "❌ Ошибка! Введите корректное число (используйте точку или запятую).\n\n"
                "Введите общий диаметр струны (в мм):",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return TOTAL_DIAM

    async def get_length(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение длины навивки"""
        logger.info(f"get_length вызван. Текст: '{update.message.text}'")

        try:
            text = update.message.text.replace(",", ".")
            length = float(text)
            logger.info(f"Преобразовано в число: {length}")

            if length <= 0:
                await update.message.reply_text(
                    "❌ Длина должна быть положительным числом!\n\n"
                    "Введите длину навивки (в мм):",
                    reply_markup=MenuBuilder.get_back_menu()
                )
                return LENGTH

            context.user_data['length'] = length
            logger.info(f"Сохранена длина: {length}")

            # ВЫПОЛНЯЕМ РАСЧЕТ
            return await self.calculate(update, context)

        except ValueError:
            await update.message.reply_text(
                "❌ Ошибка! Введите корректное число (используйте точку или запятую).\n\n"
                "Введите длину навивки (в мм):",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return LENGTH

    async def calculate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выполнение расчета"""
        logger.info("===== НАЧАЛО РАСЧЕТА =====")

        winding_type = context.user_data.get('winding_type')
        core_diam = context.user_data.get('core_diameter')
        total_diam = context.user_data.get('total_diameter')
        length = context.user_data.get('length')

        logger.info(f"Данные: тип={winding_type}, керн={core_diam}, общий={total_diam}, длина={length}")

        if None in (winding_type, core_diam, total_diam, length):
            logger.error("НЕПОЛНЫЕ ДАННЫЕ!")
            await update.message.reply_text(
                "❌ Данные неполные. Начните заново: /calculator",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return ConversationHandler.END

        try:
            calc = Calculator()

            if winding_type == 1:
                # Одиночная навивка
                copper_diam = calc.cooperDiam(total_diam, core_diam)
                copper_diam_rounded = round(copper_diam, 3)
                copper_length = calc.lengthCooper(core_diam, copper_diam, length)
                copper_length_int = int(copper_length)

                logger.info(f"РЕЗУЛЬТАТ: диаметр меди={copper_diam_rounded}, длина меди={copper_length_int}")

                await self.db.save_calculation({
                    'user_id': update.effective_user.id,
                    'winding_type': winding_type,
                    'core_diameter': core_diam,
                    'total_diameter': total_diam,
                    'length': length,
                    'primary_diam': copper_diam_rounded,
                    'secondary_diam': None,
                    'primary_length': copper_length_int,
                    'secondary_length': None
                })

                result_text = (
                    "✅ РЕЗУЛЬТАТЫ РАСЧЕТА\n"
                    "═══════════════════════\n\n"
                    f"Тип навивки: Одиночная\n"
                    f"Диаметр керна: {core_diam:.3f} мм\n"
                    f"Общий диаметр: {total_diam:.3f} мм\n"
                    f"Длина навивки: {length:.0f} мм\n\n"
                    "Расчетные параметры:\n"
                    f"Диаметр меди: {copper_diam_rounded:.3f} мм\n"
                    f"Длина меди: {copper_length_int} мм"
                )

            else:
                # Двойная навивка
                copper_first = calc.cooperFirst(total_diam, core_diam)
                copper_first_rounded = round(copper_first, 3)

                copper_second = calc.cooperSecond(total_diam, core_diam)
                copper_second_rounded = round(copper_second, 3)

                length_primary = calc.lengthCooperPrimary(core_diam, length, copper_first)
                length_primary_int = int(length_primary)

                length_secondary = calc.lengthCooperSecondary(core_diam, length, copper_first, copper_second)
                length_secondary_int = int(length_secondary)

                logger.info(f"РЕЗУЛЬТАТ: первичная={copper_first_rounded}, вторичная={copper_second_rounded}")

                await self.db.save_calculation({
                    'user_id': update.effective_user.id,
                    'winding_type': winding_type,
                    'core_diameter': core_diam,
                    'total_diameter': total_diam,
                    'length': length,
                    'primary_diam': copper_first_rounded,
                    'secondary_diam': copper_second_rounded,
                    'primary_length': length_primary_int,
                    'secondary_length': length_secondary_int
                })

                result_text = (
                    "✅ РЕЗУЛЬТАТЫ РАСЧЕТА\n"
                    "═══════════════════════\n\n"
                    f"Тип навивки: Двойная\n"
                    f"Диаметр керна: {core_diam:.3f} мм\n"
                    f"Общий диаметр: {total_diam:.3f} мм\n"
                    f"Длина навивки: {length:.0f} мм\n\n"
                    "Расчетные параметры:\n"
                    f"Диаметр первичной меди: {copper_first_rounded:.3f} мм\n"
                    f"Диаметр вторичной меди: {copper_second_rounded:.3f} мм\n\n"
                    f"Длина первичной меди: {length_primary_int} мм\n"
                    f"Длина вторичной меди: {length_secondary_int} мм"
                )

            # Очищаем контекст
            context.user_data.clear()
            logger.info("Контекст очищен")

            # Кнопки
            keyboard = [
                [InlineKeyboardButton("🔄 Новый расчет", callback_data="calculator_start")],
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # ===== ОТПРАВЛЯЕМ РЕЗУЛЬТАТ =====
            logger.info("ОТПРАВЛЯЕМ РЕЗУЛЬТАТ ПОЛЬЗОВАТЕЛЮ...")
            await update.message.reply_text(
                result_text,
                reply_markup=reply_markup,
                parse_mode="HTML"  # Используем HTML вместо Markdown
            )
            logger.info("✅ РЕЗУЛЬТАТ ОТПРАВЛЕН!")
            # =================================

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"ОШИБКА РАСЧЕТА: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(
                f"❌ Ошибка при расчете: {str(e)}\nПопробуйте снова: /calculator",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return ConversationHandler.END

    # ==================== КНОПКИ НАЗАД ====================

    async def back_to_winding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query is None:
            logger.error("callback_query is None")
            return ConversationHandler.END

        await query.answer()
        context.user_data.clear()
        logger.info("back_to_winding вызван")

        keyboard = [
            [InlineKeyboardButton("🎵 Одиночная навивка", callback_data="winding_single")],
            [InlineKeyboardButton("🎶 Двойная навивка", callback_data="winding_double")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🧮 Калькулятор басовых струн\n\n"
            "Выберите тип навивки:",
            reply_markup=reply_markup
        )
        return SELECT_WINDING

    async def back_to_core(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query is None:
            logger.error("callback_query is None")
            return ConversationHandler.END

        await query.answer()
        context.user_data.pop('core_diameter', None)
        logger.info("back_to_core вызван")

        await query.edit_message_text(
            "Введите диаметр керна (в мм):\n"
            "(например: 0.85)",
            reply_markup=MenuBuilder.get_back_menu()
        )
        return CORE_DIAM

    async def back_to_total(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query is None:
            logger.error("callback_query is None")
            return ConversationHandler.END

        await query.answer()
        context.user_data.pop('total_diameter', None)
        core_diam = context.user_data.get('core_diameter', 0)
        logger.info(f"back_to_total вызван, core_diam={core_diam}")

        await query.edit_message_text(
            f"Введите общий диаметр струны (в мм):\n"
            f"(должен быть больше {core_diam:.3f} мм)",
            reply_markup=MenuBuilder.get_back_menu()
        )
        return TOTAL_DIAM

    async def cancel_calculation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query is None:
            logger.error("callback_query is None")
            return ConversationHandler.END

        await query.answer()
        context.user_data.clear()
        logger.info("cancel_calculation вызван")

        user = await self.db.get_user(update.effective_user.id)
        is_admin = user.is_admin or user.is_super_admin if user else False

        await query.edit_message_text(
            "Расчет отменен.",
            reply_markup=MenuBuilder.get_main_menu(user, is_admin)
        )
        return ConversationHandler.END

    async def back_to_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query is None:
            logger.error("callback_query is None")
            return ConversationHandler.END

        await query.answer()
        context.user_data.clear()
        logger.info("back_to_main вызван")

        user = await self.db.get_user(update.effective_user.id)
        is_admin = user.is_admin or user.is_super_admin if user else False

        await query.edit_message_text(
            "🏠 Главное меню\n\n"
            "Выберите действие:",
            reply_markup=MenuBuilder.get_main_menu(user, is_admin)
        )
        return ConversationHandler.END