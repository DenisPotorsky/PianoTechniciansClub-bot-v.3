from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger


def admin_only(func):
    """Декоратор для ограничения доступа администраторам"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not await self.db.is_admin(user_id):
            await update.callback_query.answer("⛔️ Недостаточно прав!", show_alert=True)
            logger.warning(f"Попытка доступа к админ-функции от пользователя {user_id}")
            return
        return await func(self, update, context, *args, **kwargs)
    return wrapper


def subscribed_only(func):
    """Декоратор для ограничения доступа подписанным пользователям"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not await self.db.is_user_allowed(user_id):
            await update.callback_query.answer("🔒 Требуется подписка!", show_alert=True)
            return
        return await func(self, update, context, *args, **kwargs)
    return wrapper


def log_activity(func):
    """Декоратор для логирования активности"""
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        logger.info(f"Активность: {func.__name__} от {user.id} (@{user.username})")
        return await func(self, update, context, *args, **kwargs)
    return wrapper