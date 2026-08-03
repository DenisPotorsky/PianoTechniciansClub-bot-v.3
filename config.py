import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Конфигурация бота"""
    token: str
    super_admin: int
    admin_ids: List[int]
    channel_url: str
    chat_url: str
    channel_id: str
    chat_id: str
    database_path: str

    @classmethod
    def from_env(cls) -> 'Config':
        """Загрузка конфигурации из переменных окружения"""
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise ValueError("BOT_TOKEN не найден в .env файле")

        super_admin_str = os.getenv("SUPER_ADMIN", "")
        super_admin = int(super_admin_str) if super_admin_str else 0

        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = []
        if admin_ids_str:
            admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

        return cls(
            token=token,
            super_admin=super_admin,
            admin_ids=admin_ids,
            channel_url=os.getenv("CHANNEL_URL", ""),
            chat_url=os.getenv("CHAT_URL", ""),
            channel_id=os.getenv("CHANNEL_ID", ""),
            chat_id=os.getenv("CHAT_ID", ""),
            database_path=os.getenv("DB_PATH", "piano_club.db")
        )


config = Config.from_env()