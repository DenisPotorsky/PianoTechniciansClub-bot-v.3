#!/usr/bin/env python3
"""
PianoTechniciansClub Bot v.3
Закрытый клуб для фортепианных мастеров экстракласса
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from loguru import logger

from config import config
from database import Database
from handlers.calculator import CalculatorHandler, SELECT_WINDING, CORE_DIAM, TOTAL_DIAM, LENGTH
from handlers.club import ClubHandler
from handlers.admin import AdminHandler
from keyboard.menus import MenuBuilder


class PianoClubBot:
    def __init__(self):
        self.db = Database(config.database_path)
        self.calculator_handler = CalculatorHandler(self.db)
        self.club_handler = ClubHandler(self.db)
        self.admin_handler = AdminHandler(self.db)
        self.app = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user:
            return

        # Проверяем роли
        is_super_admin = await self.db.is_super_admin_in_env(user.id)
        is_admin = await self.db.is_admin_in_env(user.id)

        # Регистрируем пользователя
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name or "User",
            'last_name': user.last_name,
            'is_subscribed': False,
            'is_admin': is_admin,
            'is_super_admin': is_super_admin
        }

        db_user = await self.db.add_user(user_data)
        is_allowed = await self.db.is_user_allowed(user.id)
        has_admin_rights = await self.db.is_admin(user.id)

        greeting = "🎹 *Добро пожаловать в PianoTechniciansClub!*\n\n"
        greeting += "Закрытое сообщество фортепианных мастеров экстра-класса.\n\n"

        if db_user.is_super_admin:
            greeting += "👑 *Супер-администратор*\n\nВам доступны все функции бота."
        elif db_user.is_admin:
            greeting += "⭐ *Администратор*\n\nВам доступны все функции бота."
        elif is_allowed:
            greeting += "✅ *Доступ предоставлен*\n\nВы можете использовать все функции бота:\n• Калькулятор басовых струн\n• Участие в чате\n• Просмотр канала"
        else:
            greeting += (
                "🔒 *Доступ ограничен*\n\n"
                "Это закрытый клуб профессионалов.\n"
                "Для получения доступа:\n"
                "1. Нажмите на кнопку 'Запросить доступ'\n"
                "2. Отправьте заявку администратору\n"
                "3. Дождитесь одобрения\n\n"
                "Доступ предоставляется персонально."
            )

        # Уведомление админам о новом пользователе
        if not is_allowed and not db_user.is_super_admin and not db_user.is_admin:
            await self.notify_admins_about_new_user(update, context, db_user)

        await update.message.reply_text(
            greeting,
            reply_markup=MenuBuilder.get_main_menu(db_user, has_admin_rights),
            parse_mode="Markdown"
        )

        logger.info(f"Пользователь {user.id} (@{user.username}) запустил бота")

    async def notify_admins_about_new_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user):
        """Уведомление администраторов о новом пользователе"""
        admins = [config.super_admin] + config.admin_ids
        username = f"@{user.username}" if user.username else "нет"
        full_name = user.full_name

        notification = (
            f"🔔 *НОВЫЙ ПОЛЬЗОВАТЕЛЬ!*\n\n"
            f"👤 Имя: {full_name}\n"
            f"🆔 ID: `{user.user_id}`\n"
            f"📱 Username: {username}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Для управления пользователем используйте админ-панель."
        )

        for admin_id in admins:
            try:
                await context.bot.send_message(
                    admin_id,
                    notification,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить админа {admin_id}: {e}")

    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user = await self.db.get_user(update.effective_user.id)
        has_admin_rights = user.is_admin or user.is_super_admin if user else False

        await query.edit_message_text(
            "🏠 *Главное меню*\n\nВыберите действие из меню ниже:",
            reply_markup=MenuBuilder.get_main_menu(user, has_admin_rights),
            parse_mode="Markdown"
        )

    async def set_bot_commands(self):
        """Установка команд для синей кнопки меню"""
        commands = [
            BotCommand("start", "🏠 Главное меню"),
            BotCommand("about", "ℹ️ О проекте"),
            BotCommand("support", "❓ Поддержка"),
        ]

        # Админские команды доступны всем админам
        if config.super_admin or config.admin_ids:
            commands.extend([
                BotCommand("admin", "👥 Админ-панель"),
                BotCommand("stats", "📊 Статистика"),
            ])

        await self.app.bot.set_my_commands(commands)
        logger.info("✅ Команды меню установлены")

    def setup_handlers(self):
        # Базовые команды
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("about", self.club_handler.about_command))
        self.app.add_handler(CommandHandler("support", self.club_handler.support_command))
        self.app.add_handler(CommandHandler("admin", self.admin_handler.admin_users))
        self.app.add_handler(CommandHandler("stats", self.admin_handler.show_statistics))

        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(self.main_menu, pattern="^main_menu$"))
        self.app.add_handler(CallbackQueryHandler(self.club_handler.about, pattern="^about$"))
        self.app.add_handler(CallbackQueryHandler(self.club_handler.request_access, pattern="^request_access$"))
        self.app.add_handler(CallbackQueryHandler(self.club_handler.send_request, pattern="^send_request$"))
        self.app.add_handler(CallbackQueryHandler(self.club_handler.channel, pattern="^channel$"))
        self.app.add_handler(CallbackQueryHandler(self.club_handler.chat, pattern="^chat$"))
        self.app.add_handler(CallbackQueryHandler(self.club_handler.support, pattern="^support$"))

        # Админские обработчики
        self.app.add_handler(CallbackQueryHandler(self.admin_handler.admin_users, pattern="^admin_users$"))
        self.app.add_handler(CallbackQueryHandler(self.admin_handler.handle_admin_page, pattern="^admin_page_"))
        self.app.add_handler(CallbackQueryHandler(self.admin_handler.handle_user_action, pattern="^admin_user_"))
        self.app.add_handler(
            CallbackQueryHandler(self.admin_handler.toggle_user_subscription, pattern="^admin_toggle_"))
        self.app.add_handler(CallbackQueryHandler(self.admin_handler.approve_request, pattern="^approve_"))
        self.app.add_handler(CallbackQueryHandler(self.admin_handler.reject_request, pattern="^reject_"))
        self.app.add_handler(CallbackQueryHandler(self.admin_handler.show_statistics, pattern="^admin_stats$"))
        self.app.add_handler(CallbackQueryHandler(self.admin_handler.broadcast_start, pattern="^admin_broadcast$"))

        # ==================== КАЛЬКУЛЯТОР ====================
        # Создаем ConversationHandler для калькулятора
        calc_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.calculator_handler.start_calculation, pattern="^calculator_start$"),
                CommandHandler("calculator", self.calculator_handler.start_command),
            ],
            states={
                SELECT_WINDING: [
                    CallbackQueryHandler(self.calculator_handler.select_winding, pattern="^winding_(single|double)$"),
                    CallbackQueryHandler(self.calculator_handler.back_to_main, pattern="^main_menu$"),
                ],
                CORE_DIAM: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.calculator_handler.get_core_diameter),
                    CallbackQueryHandler(self.calculator_handler.back_to_winding, pattern="^back_to_winding$"),
                    CallbackQueryHandler(self.calculator_handler.back_to_main, pattern="^main_menu$"),
                ],
                TOTAL_DIAM: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.calculator_handler.get_total_diameter),
                    CallbackQueryHandler(self.calculator_handler.back_to_core, pattern="^back_to_core$"),
                    CallbackQueryHandler(self.calculator_handler.back_to_main, pattern="^main_menu$"),
                ],
                LENGTH: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.calculator_handler.get_length),
                    CallbackQueryHandler(self.calculator_handler.back_to_total, pattern="^back_to_total$"),
                    CallbackQueryHandler(self.calculator_handler.back_to_main, pattern="^main_menu$"),
                ],
            },
            fallbacks=[
                CallbackQueryHandler(self.calculator_handler.cancel_calculation, pattern="^(main_menu|calc_cancel)$"),
                CommandHandler("start", self.start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.calculator_handler.cancel_calculation),
            ],
            allow_reentry=True,
            per_message=False,
        )
        self.app.add_handler(calc_conv_handler)

        # Обработчик для broadcast (должен быть после ConversationHandler)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_handler.broadcast_message))

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Ошибка: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже.",
                reply_markup=MenuBuilder.get_back_menu()
            )

    async def run_async(self):
        self.app = Application.builder().token(config.token).build()
        self.setup_handlers()
        self.app.add_error_handler(self.error_handler)

        await self.set_bot_commands()

        logger.info("🚀 Бот запущен!")
        logger.info(f"👑 Супер-админ: {config.super_admin}")
        logger.info(f"⭐ Админы: {config.admin_ids}")

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("👋 Бот остановлен")
        finally:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

    def run(self):
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            logger.info("👋 Бот остановлен")
        except Exception as e:
            logger.error(f"Ошибка при запуске: {e}")
            sys.exit(1)


def main():
    bot = PianoClubBot()
    bot.run()


if __name__ == "__main__":
    main()