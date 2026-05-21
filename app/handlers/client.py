"""Сообщения от клиентов: форвард владельцу + автоответ клиенту."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.types import Message

from ..config import settings
from ..db import Database
from ..remnawave import RemnawaveClient
from ..texts import caption_for_owner

logger = logging.getLogger(__name__)

# Только личка. Группы и каналы игнорим — бот не для них.
router = Router(name="client")
router.message.filter(F.chat.type == "private")


@router.message()
async def relay_to_owner(
    message: Message,
    bot: Bot,
    db: Database,
    remnawave: RemnawaveClient,
) -> None:
    if message.from_user is None:
        return
    if message.from_user.id == settings.owner_tg_id:
        # Владелец — его сообщения обрабатывает owner.py. Сюда попадёт, только если
        # владелец что-то написал без reply — тогда подскажем, как пользоваться.
        from ..texts import OWNER_REPLY_HINT
        await message.answer(OWNER_REPLY_HINT, parse_mode="Markdown")
        return

    tg_id = message.from_user.id
    tg_username = message.from_user.username

    # 1. Тянем (или нет) данные подписки из Remnawave.
    user_record = await db.get_user(tg_id)
    rw_user = None
    if user_record and user_record.remnawave_uuid:
        rw_user = await remnawave.get_user_by_uuid(user_record.remnawave_uuid)

    # Запоминаем/обновляем юзера, чтобы не терять username между сессиями.
    await db.upsert_user(tg_user_id=tg_id, tg_username=tg_username)

    # 2. Шлём контекст владельцу отдельным сообщением.
    caption_msg = await bot.send_message(
        chat_id=settings.owner_tg_id,
        text=caption_for_owner(rw_user, tg_username, tg_id),
        parse_mode="Markdown",
    )

    # 3. Форвардим оригинал клиента владельцу. Именно на ЭТО сообщение владелец
    # будет делать Reply, чтобы ответить.
    forwarded = await bot.forward_message(
        chat_id=settings.owner_tg_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )

    # Запоминаем связку: каждое из двух сообщений у владельца ведёт к клиенту.
    # Это позволяет владельцу делать reply на любое из них.
    await db.save_link(
        owner_msg_id=forwarded.message_id,
        client_tg_id=tg_id,
        client_msg_id=message.message_id,
    )
    await db.save_link(
        owner_msg_id=caption_msg.message_id,
        client_tg_id=tg_id,
        client_msg_id=message.message_id,
    )

    # 4. Клиенту — автоответ.
    await message.answer(settings.autoreply_text)
