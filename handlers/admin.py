from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from database import Database
from keyboard.menus import MenuBuilder
from config import config
from datetime import datetime


class AdminHandler:
    def __init__(self, db: Database):
        self.db = db

    async def check_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        user = await self.db.get_user(update.effective_user.id)
        if not user or not (user.is_super_admin or user.is_admin):
            if update.callback_query:
                await update.callback_query.answer("⛔️ Недостаточно прав!", show_alert=True)
            else:
                await update.message.reply_text("⛔️ Недостаточно прав!")
            return False
        return True

    async def admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Управление пользователями"""
        if not await self.check_admin(update, context):
            return

        query = update.callback_query
        if query is None:
            return

        await query.answer()

        users = await self.db.get_all_users()
        context.user_data['admin_users'] = users
        context.user_data['admin_page'] = 0

        current_user = await self.db.get_user(update.effective_user.id)
        is_super_admin = current_user.is_super_admin if current_user else False

        users_data = []
        for user in users:
            users_data.append({
                'user_id': user.user_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_subscribed': user.is_subscribed,
                'is_admin': user.is_admin,
                'is_super_admin': user.is_super_admin,
                'full_name': user.full_name
            })

        text = (
            "👥 Управление пользователями\n\n"
            f"Всего: {len(users_data)}\n"
            f"👑 Супер-админ: 1\n"
            f"⭐ Админов: {sum(1 for u in users_data if u['is_admin'] and not u['is_super_admin'])}\n"
            f"✅ Участников: {sum(1 for u in users_data if u['is_subscribed'] and not u['is_admin'] and not u['is_super_admin'])}\n"
            f"❌ Не зарегистрировано: {sum(1 for u in users_data if not u['is_subscribed'] and not u['is_admin'] and not u['is_super_admin'])}"
        )

        await query.edit_message_text(
            text,
            reply_markup=MenuBuilder.get_admin_users_menu(users_data, 0, is_super_admin)
        )

    async def handle_admin_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_admin(update, context):
            return

        query = update.callback_query
        if query is None:
            return

        await query.answer()

        page = int(query.data.split('_')[-1])
        context.user_data['admin_page'] = page
        users = context.user_data.get('admin_users', [])

        users_data = []
        for user in users:
            users_data.append({
                'user_id': user.user_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_subscribed': user.is_subscribed,
                'is_admin': user.is_admin,
                'is_super_admin': user.is_super_admin,
                'full_name': user.full_name
            })

        current_user = await self.db.get_user(update.effective_user.id)
        is_super_admin = current_user.is_super_admin if current_user else False

        await query.edit_message_text(
            f"👥 Управление пользователями\n\nВсего: {len(users_data)}",
            reply_markup=MenuBuilder.get_admin_users_menu(users_data, page, is_super_admin)
        )

    async def handle_user_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_admin(update, context):
            return

        query = update.callback_query
        if query is None:
            return

        await query.answer()

        user_id = int(query.data.split('_')[-1])

        # Проверяем, не тот ли это пользователь, что уже выбран
        selected_user = context.user_data.get('selected_user')
        if selected_user == user_id:
            return

        # Получаем объект пользователя из БД
        user = await self.db.get_user(user_id)

        if not user:
            await query.edit_message_text("❌ Пользователь не найден", reply_markup=MenuBuilder.get_back_menu())
            return

        context.user_data['selected_user'] = user_id

        if user.is_super_admin:
            status = "👑 Супер-админ"
        elif user.is_admin:
            status = "⭐ Админ"
        elif user.is_subscribed:
            status = "✅ Участник клуба"
        else:
            status = "❌ Не зарегистрирован"

        text = (
            f"👤 Информация о пользователе\n\n"
            f"Имя: {user.full_name}\n"
            f"ID: {user.user_id}\n"
            f"Username: @{user.username or 'нет'}\n"
            f"Статус: {status}\n"
            f"Дата регистрации: {user.joined_at.strftime('%d.%m.%Y %H:%M') if user.joined_at else 'неизвестно'}"
        )

        # Передаем объект user
        await query.edit_message_text(
            text,
            reply_markup=MenuBuilder.get_user_action_menu(user, update.effective_user.id)
        )

    async def toggle_user_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_admin(update, context):
            return

        query = update.callback_query
        if query is None:
            return

        await query.answer()

        user_id = int(query.data.split('_')[-1])
        user = await self.db.get_user(user_id)

        if not user:
            await query.edit_message_text("❌ Пользователь не найден", reply_markup=MenuBuilder.get_back_menu())
            return

        if user.is_super_admin or user.is_admin:
            await query.edit_message_text(
                "❌ Нельзя управлять администраторами!",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return

        new_status = not user.is_subscribed
        await self.db.toggle_subscription(user_id, new_status)

        status_text = "✅ добавлена" if new_status else "❌ удалена"
        action_text = "добавлен в клуб" if new_status else "удален из клуба"

        try:
            await context.bot.send_message(
                user_id,
                f"🔔 Изменение статуса в клубе\n\nВы были {action_text} администратором."
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить {user_id}: {e}")

        context.user_data.pop('selected_user', None)

        await query.edit_message_text(
            f"✅ Подписка {status_text} для {user.full_name}",
            reply_markup=MenuBuilder.get_back_menu()
        )

    async def approve_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_admin(update, context):
            return

        query = update.callback_query
        if query is None:
            return

        await query.answer()

        user_id = int(query.data.split('_')[-1])
        user = await self.db.get_user(user_id)

        if not user:
            await query.edit_message_text("❌ Пользователь не найден")
            return

        await self.db.toggle_subscription(user_id, True)

        try:
            await context.bot.send_message(
                user_id,
                "🎉 Поздравляем!\n\nВаша заявка на вступление в клуб одобрена!\nТеперь вам доступны все функции бота.\n\nДобро пожаловать в PianoTechniciansClub! 🎹"
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить {user_id}: {e}")

        await query.edit_message_text(
            f"✅ Заявка пользователя {user.full_name} одобрена!",
            reply_markup=MenuBuilder.get_back_menu()
        )

        await query.message.edit_reply_markup(reply_markup=None)

    async def reject_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_admin(update, context):
            return

        query = update.callback_query
        if query is None:
            return

        await query.answer()

        user_id = int(query.data.split('_')[-1])
        user = await self.db.get_user(user_id)

        if not user:
            await query.edit_message_text("❌ Пользователь не найден")
            return

        try:
            await context.bot.send_message(
                user_id,
                "❌ К сожалению\n\nВаша заявка на вступление в клуб была отклонена."
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить {user_id}: {e}")

        await query.edit_message_text(
            f"❌ Заявка пользователя {user.full_name} отклонена.",
            reply_markup=MenuBuilder.get_back_menu()
        )

        await query.message.edit_reply_markup(reply_markup=None)

    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_admin(update, context):
            return

        query = update.callback_query
        if query is None:
            return

        await query.answer()

        stats = await self.db.get_statistics()
        users = await self.db.get_all_users()

        admins_count = sum(1 for u in users if u.is_admin)
        super_admin_count = sum(1 for u in users if u.is_super_admin)
        subscribed_count = sum(1 for u in users if u.is_subscribed and not u.is_admin and not u.is_super_admin)

        text = (
            f"📊 Статистика бота\n\n"
            f"👥 Всего пользователей: {stats['total_users']}\n"
            f"👑 Супер-админ: {super_admin_count}\n"
            f"⭐ Админов: {admins_count}\n"
            f"✅ Участников: {subscribed_count}\n"
            f"❌ Не зарегистрировано: {stats['total_users'] - super_admin_count - admins_count - subscribed_count}\n\n"
            f"📊 Всего расчетов: {stats['total_calculations']}\n"
            f"📈 Активных сегодня: {stats['active_today']}"
        )

        if stats['total_users'] > 0:
            text += f"\n\n🔄 Конверсия: {stats['subscribed_users'] / stats['total_users'] * 100:.1f}%"

        await query.edit_message_text(
            text,
            reply_markup=MenuBuilder.get_back_menu()
        )

    async def broadcast_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_admin(update, context):
            return

        query = update.callback_query
        if query is None:
            return

        await query.answer()

        context.user_data['broadcast_mode'] = True
        await query.edit_message_text(
            "📨 Рассылка сообщений\n\nВведите текст для рассылки всем участникам клуба:",
            reply_markup=MenuBuilder.get_back_menu()
        )

    async def broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.user_data.get('broadcast_mode'):
            return

        user = await self.db.get_user(update.effective_user.id)
        if not user or not (user.is_super_admin or user.is_admin):
            await update.message.reply_text("⛔️ Недостаточно прав!")
            return

        text = update.message.text
        context.user_data['broadcast_mode'] = False

        users = await self.db.get_subscribed_users()

        if not users:
            await update.message.reply_text(
                "❌ Нет подписанных пользователей для рассылки.",
                reply_markup=MenuBuilder.get_back_menu()
            )
            return

        sent = 0
        progress_msg = await update.message.reply_text(f"📤 Отправка... 0/{len(users)}")

        for i, user in enumerate(users):
            try:
                await context.bot.send_message(user.user_id, text)
                sent += 1
            except Exception as e:
                logger.error(f"Ошибка {user.user_id}: {e}")

            if (i + 1) % 5 == 0 or (i + 1) == len(users):
                await progress_msg.edit_text(f"📤 Отправка... {i + 1}/{len(users)}")

        await progress_msg.edit_text(
            f"✅ Рассылка завершена!\n📨 Отправлено: {sent}\n👥 Всего: {len(users)}",
            reply_markup=MenuBuilder.get_back_menu()
        )