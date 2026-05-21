"""Ответы владельца через Reply — доставка клиенту."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.types import Message

from ..config import settings
from ..db import Database
from ..texts import DELIVERED, NOT_LINKED_REPLY, OWNER_REPLY_HINT

logger = logging.getLogger(__name__)

# Этот router срабатывает только когда пишет владелец в личку боту.
router = Router(name="owner")
router.message.filter(F.chat.type == "private", F.from_user.id == settings.owner_tg_id)


@router.message(F.reply_to_message)
async def owner_reply(message: Message, bot: Bot, db: Database) -> None:
    if message.reply_to_message is None:
        return
    link = await db.find_client_by_owner_msg(message.reply_to_message.message_id)
    if link is None:
        await message.reply(NOT_LINKED_REPLY)
        return

    # Копируем сообщение владельца клиенту. copy_message сохраняет тип (текст/фото/
    # документ/голос), но не показывает клиенту, что это "переслано" — клиент видит
    # обычное сообщение от бота поддержки.
    sent = await bot.copy_message(
        chat_id=link.client_tg_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )

    # На будущее: если клиент сделает reply на этот наш ответ — мы тоже сможем
    # отследить thread. Но пока нам этого не нужно.
    logger.info("Delivered owner reply to tg_id=%s as msg_id=%s", link.client_tg_id, sent.message_id)
    await message.reply(DELIVERED)


@router.message()
async def owner_without_reply(message: Message) -> None:
    """Владелец написал боту что-то без reply — подсказываем, как пользоваться."""
    # Игнорим команды (например /start), их обработают свои handlers.
    if message.text and message.text.startswith("/"):
        return
    await message.answer(OWNER_REPLY_HINT)
