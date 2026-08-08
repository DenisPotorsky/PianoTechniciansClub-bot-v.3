from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict


class MenuBuilder:
    """Построитель меню"""

    @staticmethod
    def get_main_menu(user, is_admin: bool = False) -> InlineKeyboardMarkup:
        """Главное меню бота"""
        keyboard = []

        keyboard.append([InlineKeyboardButton("ℹ️ О проекте", callback_data="about")])

        if user and (user.is_super_admin or user.is_admin or user.is_subscribed):
            keyboard.append([InlineKeyboardButton("📢 Канал", callback_data="channel")])
            keyboard.append([InlineKeyboardButton("💬 Чат", callback_data="chat")])
            keyboard.append([InlineKeyboardButton("🧮 Калькулятор басовых струн", callback_data="calculator_start")])
            keyboard.append([InlineKeyboardButton("🔍 Определить возраст инструмента", callback_data="age_start")])  #
            # НОВАЯ КНОПКА
        else:
            keyboard.append([InlineKeyboardButton("🔑 Запросить доступ", callback_data="request_access")])

        if is_admin:
            keyboard.extend([
                [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_users")],
                [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
                [InlineKeyboardButton("📨 Рассылка", callback_data="admin_broadcast")],
            ])

        keyboard.append([InlineKeyboardButton("❓ Поддержка", callback_data="support")])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_back_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_calculator_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🎵 Одиночная навивка", callback_data="winding_single")],
            [InlineKeyboardButton("🎶 Двойная навивка", callback_data="winding_double")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_admin_users_menu(users: List[Dict], page: int = 0, is_super_admin: bool = False) -> InlineKeyboardMarkup:
        keyboard = []
        per_page = 5
        start = page * per_page
        end = min(start + per_page, len(users))

        for user in users[start:end]:
            if user.get('is_super_admin'):
                status = "👑"
                name = f"{user.get('full_name', 'Unknown')} (Супер-админ)"
            elif user.get('is_admin'):
                status = "⭐"
                name = f"{user.get('full_name', 'Unknown')} (Админ)"
            elif user.get('is_subscribed'):
                status = "✅"
                name = user.get('full_name', 'Unknown')
            else:
                status = "❌"
                name = user.get('full_name', 'Unknown')

            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {name}",
                    callback_data=f"admin_user_{user.get('user_id')}"
                )
            ])

        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"admin_page_{page - 1}"))
        if end < len(users):
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"admin_page_{page + 1}"))
        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_user_action_menu(user, current_user_id: int) -> InlineKeyboardMarkup:
        keyboard = []

        if user and hasattr(user, 'is_super_admin') and hasattr(user, 'is_admin'):
            if not user.is_super_admin and not user.is_admin:
                action = "🔴 Удалить из клуба" if user.is_subscribed else "🟢 Добавить в клуб"
                keyboard.append([InlineKeyboardButton(action, callback_data=f"admin_toggle_{user.user_id}")])
            else:
                keyboard.append([InlineKeyboardButton("ℹ️ Нельзя управлять", callback_data="admin_no_action")])
        else:
            keyboard.append([InlineKeyboardButton("ℹ️ Нельзя управлять", callback_data="admin_no_action")])

        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_users")])
        return InlineKeyboardMarkup(keyboard)