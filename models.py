from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Модель пользователя"""
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    is_subscribed: bool = False
    is_admin: bool = False
    is_super_admin: bool = False
    joined_at: Optional[datetime] = None
    subscribed_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def display_name(self) -> str:
        """Имя для отображения"""
        if self.username:
            return f"@{self.username}"
        return self.full_name

    @property
    def role(self) -> str:
        """Роль пользователя"""
        if self.is_super_admin:
            return "👑 Супер-админ"
        elif self.is_admin:
            return "⭐ Админ"
        elif self.is_subscribed:
            return "✅ Участник"
        else:
            return "❌ Не зарегистрирован"