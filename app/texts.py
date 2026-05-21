"""Все тексты сообщений собраны в одном месте — удобно редактировать.

Везде используется HTML parse_mode (он надёжнее Markdown — не падает на _ и * в username).
"""

from __future__ import annotations

from html import escape
from typing import Optional

from .remnawave import RemnawaveUser


WELCOME_LINKED = (
    "👋 Привет! Вы привязаны к подписке <b>{username}</b>.\n\n"
    "Напишите сюда любой вопрос — администратор скоро ответит."
)

WELCOME_UNLINKED = (
    "👋 Привет! Это бот поддержки.\n\n"
    "Напишите сюда любой вопрос. Если вы — клиент, "
    "укажите ваш <b>username</b> из подписки или email, чтобы администратор быстрее вас нашёл."
)

OWNER_BANNER = "👤 Бот поддержки запущен. Все сообщения клиентов будут приходить сюда."

OWNER_REPLY_HINT = (
    "ℹ️ Чтобы ответить клиенту — сделайте <b>Reply</b> на форварднутое сообщение и напишите ответ.\n"
    "Любое сообщение без reply я <i>не</i> пересылаю."
)

DELIVERED = "✅ Ответ доставлен клиенту."

NOT_LINKED_REPLY = (
    "⚠️ Не вижу, к какому клиенту этот reply. Возможно, история была очищена.\n"
    "Попросите клиента написать заново и ответьте на новое сообщение."
)


def caption_for_owner(user: Optional[RemnawaveUser], tg_username: Optional[str], tg_id: int) -> str:
    """HTML-caption, который бот добавляет ОТДЕЛЬНЫМ сообщением перед форвардом клиента.

    Сам форвард Telegram трогать не даёт (метаданные форварда фиксированы),
    поэтому контекст шлём отдельным сообщением сразу перед форвардом.
    """
    if tg_username:
        tg_part = f"@{escape(tg_username)}"
    else:
        # Кликабельная ссылка на профиль клиента.
        tg_part = f'<a href="tg://user?id={tg_id}">{tg_id}</a>'

    if user is None:
        return (
            "📩 <b>Новое обращение</b>\n"
            f"От: {tg_part} (tg_id: <code>{tg_id}</code>)\n"
            "⚠️ Не привязан к подписке."
        )

    status_emoji = {
        "ACTIVE": "🟢",
        "DISABLED": "⛔",
        "LIMITED": "🟡",
        "EXPIRED": "🔴",
    }.get(user.status, "⚪")

    return (
        "📩 <b>Новое обращение</b>\n"
        f"От: {tg_part} (tg_id: <code>{tg_id}</code>)\n"
        f"Подписка: <b>{escape(user.username)}</b> {status_emoji} {escape(user.status)}\n"
        f"Истекает: {escape(user.expire_human)}\n"
        f"Трафик: {escape(user.traffic_human)}\n"
        f"UUID: <code>{escape(user.uuid)}</code>"
    )
