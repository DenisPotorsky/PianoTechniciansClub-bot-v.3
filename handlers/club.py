from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from keyboard.menus import MenuBuilder
from config import config
from datetime import datetime


class ClubHandler:
    def __init__(self, db: Database):
        self.db = db

    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /about"""
        user = await self.db.get_user(update.effective_user.id)
        is_admin = False
        if user:
            is_admin = user.is_admin or user.is_super_admin

        text = (
            "🎹 *О проекте PianoTechniciansClub*\n\n"
            "Закрытое сообщество для фортепианных мастеров экстра-класса.\n\n"
            "✨ *Наша миссия*:\n"
            "• Объединять профессионалов высочайшего уровня\n"
            "• Обмениваться уникальным опытом\n"
            "• Развивать искусство настройки фортепиано\n\n"
            "💎 *Преимущества*:\n"
            "• Эксклюзивный доступ к материалам\n"
            "• Калькулятор басовых струн\n"
            "• Закрытое сообщество профессионалов\n\n"
            "🚀 Доступ предоставляется администратором."
        )

        await update.message.reply_text(
            text,
            reply_markup=MenuBuilder.get_main_menu(user, is_admin)
        )

    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user = await self.db.get_user(update.effective_user.id)
        is_admin = False
        if user:
            is_admin = user.is_admin or user.is_super_admin

        text = (
            "🎹 *О проекте PianoTechniciansClub*\n\n"
            "Закрытое сообщество для фортепианных мастеров экстра-класса.\n\n"
            "✨ *Наша миссия*:\n"
            "• Объединять профессионалов высочайшего уровня\n"
            "• Обмениваться уникальным опытом\n"
            "• Развивать искусство настройки фортепиано\n\n"
            "💎 *Преимущества*:\n"
            "• Эксклюзивный доступ к материалам\n"
            "• Калькулятор басовых струн\n"
            "• Закрытое сообщество профессионалов\n\n"
            "🚀 Доступ предоставляется администратором."
        )

        await query.edit_message_text(
            text,
            reply_markup=MenuBuilder.get_main_menu(user, is_admin)
        )

    async def support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /support"""
        user = await self.db.get_user(update.effective_user.id)
        is_admin = False
        if user:
            is_admin = user.is_admin or user.is_super_admin

        text = (
            "❓ Помощь и поддержка\n\n"
            "📖 Инструкция для участников PianoTechniciansClub:\n\n"
            "🔑 КАК ПОЛУЧИТЬ ДОСТУП В КЛУБ\n"
            "1. Найдите бота в Telegram: @PianoTechniciansClubbot и нажмите кнопку Start (или отправьте команду /start).\n"
            "2. В главном меню нажмите кнопку 🔑 Запросить доступ, затем 📨 Отправить заявку.\n"
            "3. Дождитесь одобрения администратора. Вы получите уведомление о решении.\n\n"
            "✅ ЧТО ДОСТУПНО УЧАСТНИКАМ КЛУБА\n"
            "📢 Канал — закрытый канал с материалами клуба\n"
            "💬 Чат — общение с мастерами в закрытом чате\n"
            "🧮 Калькулятор струн — расчёт параметров басовых струн\n\n"
            "🧮 КАК ПОЛЬЗОВАТЬСЯ КАЛЬКУЛЯТОРОМ СТРУН\n"
            "1. Нажмите 🧮 Калькулятор струн в главном меню.\n"
            "2. Выберите тип навивки: 🎵 Одиночная или 🎶 Двойная.\n"
            "3. Введите параметры струны:\n"
            "   • Диаметр керна (мм) — например, 0.85\n"
            "   • Общий диаметр (мм) — например, 1.25\n"
            "   • Длина струны (мм) — например, 950\n"
            "4. Получите результат: диаметр и длина меди для изготовления струны.\n\n"
            "📌 ВАЖНО\n"
            "🔒 Клуб закрытый — доступ только по решению администратора.\n"
            "📨 Все уведомления приходят автоматически.\n"
            "🔄 Если заявка отклонена, вы можете отправить новую через 🔑 Запросить доступ.\n\n"
            "📧 КОНТАКТЫ АДМИНИСТРАЦИИ\n"
            "✉️ Email: denis-s2@yandex.ru\n"
            "💬 Telegram: @DenPotorsky\n\n"
            "По всем вопросам обращайтесь к администратору.\n"
            "Ответ в течение 24 часов.\n\n"
            "Добро пожаловать в PianoTechniciansClub! 🎹✨"
        )

        await update.message.reply_text(
            text,
            reply_markup=MenuBuilder.get_main_menu(user, is_admin)
        )

    async def support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Поддержка (callback)"""
        query = update.callback_query
        await query.answer()

        user = await self.db.get_user(update.effective_user.id)
        is_admin = False
        if user:
            is_admin = user.is_admin or user.is_super_admin

        text = (
            "❓ Помощь и поддержка\n\n"
            "📖 Инструкция для участников PianoTechniciansClub:\n\n"
            "🔑 КАК ПОЛУЧИТЬ ДОСТУП В КЛУБ\n"
            "1. Найдите бота в Telegram: @PianoTechniciansClubbot и нажмите кнопку Start (или отправьте команду /start).\n"
            "2. В главном меню нажмите кнопку 🔑 Запросить доступ, затем 📨 Отправить заявку.\n"
            "3. Дождитесь одобрения администратора. Вы получите уведомление о решении.\n\n"
            "✅ ЧТО ДОСТУПНО УЧАСТНИКАМ КЛУБА\n"
            "📢 Канал — закрытый канал с материалами клуба\n"
            "💬 Чат — общение с мастерами в закрытом чате\n"
            "🧮 Калькулятор струн — расчёт параметров басовых струн\n\n"
            "🧮 КАК ПОЛЬЗОВАТЬСЯ КАЛЬКУЛЯТОРОМ СТРУН\n"
            "1. Нажмите 🧮 Калькулятор струн в главном меню.\n"
            "2. Выберите тип навивки: 🎵 Одиночная или 🎶 Двойная.\n"
            "3. Введите параметры струны:\n"
            "   • Диаметр керна (мм) — например, 0.85\n"
            "   • Общий диаметр (мм) — например, 1.25\n"
            "   • Длина струны (мм) — например, 950\n"
            "4. Получите результат: диаметр и длина меди для изготовления струны.\n\n"
            "📌 ВАЖНО\n"
            "🔒 Клуб закрытый — доступ только по решению администратора.\n"
            "📨 Все уведомления приходят автоматически.\n"
            "🔄 Если заявка отклонена, вы можете отправить новую через 🔑 Запросить доступ.\n\n"
            "📧 КОНТАКТЫ АДМИНИСТРАЦИИ\n"
            "✉️ Email: denis-s2@yandex.ru\n"
            "💬 Telegram: @DenPotorsky\n\n"
            "По всем вопросам обращайтесь к администратору.\n"
            "Ответ в течение 24 часов.\n\n"
            "Добро пожаловать в PianoTechniciansClub! 🎹✨"
        )

        await query.edit_message_text(
            text,
            reply_markup=MenuBuilder.get_main_menu(user, is_admin)
        )

    async def request_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запрос доступа"""
        query = update.callback_query
        await query.answer()

        user = await self.db.get_user(update.effective_user.id)
        is_admin = False
        if user:
            is_admin = user.is_admin or user.is_super_admin

        if user and (user.is_subscribed or user.is_admin or user.is_super_admin):
            await query.edit_message_text(
                "✅ Вы уже являетесь участником клуба!\n\nВам доступны все функции бота.",
                reply_markup=MenuBuilder.get_main_menu(user, is_admin)
            )
            return

        text = (
            "🔑 Запрос доступа в клуб\n\n"
            "Для получения доступа к закрытому клубу, отправьте заявку администратору.\n\n"
            "После отправки заявки:\n"
            "• Администратор рассмотрит вашу заявку\n"
            "• Вы получите уведомление о решении\n"
            "• При положительном решении вам откроется доступ ко всем функциям"
        )

        keyboard = [
            [InlineKeyboardButton("📨 Отправить заявку", callback_data="send_request")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def send_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправка заявки администратору"""
        query = update.callback_query
        await query.answer()

        user = update.effective_user
        user_data = await self.db.get_user(user.id)

        if user_data and (user_data.is_subscribed or user_data.is_admin or user_data.is_super_admin):
            await query.edit_message_text(
                "✅ Вы уже являетесь участником клуба!",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return

        context.user_data['request_pending'] = True

        admins = [config.super_admin] + config.admin_ids
        username = f"@{user.username}" if user.username else "нет"
        full_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name

        request_text = (
            f"📨 НОВАЯ ЗАЯВКА НА ВСТУПЛЕНИЕ!\n\n"
            f"👤 Имя: {full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📱 Username: {username}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Нажмите на кнопку ниже, чтобы принять заявку:"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Принять", callback_data=f"approve_{user.id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        for admin_id in admins:
            try:
                await context.bot.send_message(
                    admin_id,
                    request_text,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")

        await query.edit_message_text(
            "✅ Заявка отправлена!\n\n"
            "Администратор рассмотрит вашу заявку в ближайшее время.\n"
            "Вы получите уведомление о решении.",
            reply_markup=MenuBuilder.get_back_menu()
        )

    async def channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Переход в канал"""
        query = update.callback_query
        await query.answer()

        channel_url = config.channel_url

        if not channel_url:
            await query.edit_message_text(
                "❌ Ссылка на канал не настроена.",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return

        keyboard = [
            [InlineKeyboardButton("📢 Перейти в канал", url=channel_url)],
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]

        await query.edit_message_text(
            "📢 Наш канал\n\nНажмите на кнопку ниже:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Переход в чат"""
        query = update.callback_query
        await query.answer()

        chat_url = config.chat_url

        if not chat_url:
            await query.edit_message_text(
                "❌ Ссылка на чат не настроена.",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return

        keyboard = [
            [InlineKeyboardButton("💬 Перейти в чат", url=chat_url)],
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]

        await query.edit_message_text(
            "💬 Наш чат\n\nНажмите на кнопку ниже:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )