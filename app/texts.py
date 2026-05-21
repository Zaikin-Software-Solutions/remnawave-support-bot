"""Все тексты сообщений собраны в одном месте — удобно редактировать."""

from __future__ import annotations

from typing import Optional

from .remnawave import RemnawaveUser


WELCOME_LINKED = (
    "👋 Привет! Вы привязаны к подписке *{username}*.\n\n"
    "Напишите сюда любой вопрос — администратор скоро ответит."
)

WELCOME_UNLINKED = (
    "👋 Привет! Это бот поддержки.\n\n"
    "Напишите сюда любой вопрос. Если вы — клиент, "
    "укажите ваш *username* из подписки или email, чтобы администратор быстрее вас нашёл."
)

OWNER_BANNER = "👤 Бот поддержки запущен. Все сообщения клиентов будут приходить сюда."

OWNER_REPLY_HINT = (
    "ℹ️ Чтобы ответить клиенту — сделайте *Reply* на форварднутое сообщение и напишите ответ.\n"
    "Любое сообщение без reply я *не* пересылаю."
)

DELIVERED = "✅ Ответ доставлен клиенту."

NOT_LINKED_REPLY = (
    "⚠️ Не вижу, к какому клиенту этот reply. Возможно, история была очищена.\n"
    "Попросите клиента написать заново и ответьте на новое сообщение."
)


def caption_for_owner(user: Optional[RemnawaveUser], tg_username: Optional[str], tg_id: int) -> str:
    """Caption, который бот добавляет ОТДЕЛЬНЫМ сообщением перед форвардом клиента.

    Сам форвард Telegram трогать не даёт (метаданные форварда фиксированы),
    поэтому контекст шлём отдельным сообщением сразу перед форвардом.
    """
    tg_part = f"@{tg_username}" if tg_username else f"tg://user?id={tg_id}"
    if user is None:
        return (
            f"📩 *Новое обращение*\n"
            f"От: {tg_part} (tg_id: `{tg_id}`)\n"
            f"⚠️ Не привязан к подписке."
        )
    status_emoji = {
        "ACTIVE": "🟢",
        "DISABLED": "⛔",
        "LIMITED": "🟡",
        "EXPIRED": "🔴",
    }.get(user.status, "⚪")
    return (
        f"📩 *Новое обращение*\n"
        f"От: {tg_part} (tg_id: `{tg_id}`)\n"
        f"Подписка: *{user.username}* {status_emoji} {user.status}\n"
        f"Истекает: {user.expire_human}\n"
        f"Трафик: {user.traffic_human}\n"
        f"UUID: `{user.uuid}`"
    )
