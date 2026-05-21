"""Обработка /start (в т.ч. deep-link ?start=sub_<shortUuid>)."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

from ..config import settings
from ..db import Database
from ..remnawave import RemnawaveClient
from ..texts import OWNER_BANNER, WELCOME_LINKED, WELCOME_UNLINKED

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    db: Database,
    remnawave: RemnawaveClient,
) -> None:
    # Привет владельцу — отдельно, ему deep-link не нужен.
    if message.from_user and message.from_user.id == settings.owner_tg_id:
        await message.answer(OWNER_BANNER)
        return

    if message.from_user is None:
        return  # сервисное сообщение, игнорим

    tg_id = message.from_user.id
    tg_username = message.from_user.username

    # Разбор payload: sub_<shortUuid>
    payload = (command.args or "").strip()
    linked_username: str | None = None

    if payload.startswith("sub_"):
        short_uuid = payload[len("sub_"):]
        user = await remnawave.get_user_by_short_uuid(short_uuid)
        if user is not None:
            await db.upsert_user(
                tg_user_id=tg_id,
                tg_username=tg_username,
                remnawave_uuid=user.uuid,
                short_uuid=user.short_uuid,
            )
            linked_username = user.username
            logger.info("Linked tg_id=%s -> remnawave uuid=%s", tg_id, user.uuid)

    if linked_username is None:
        # Просто запоминаем факт обращения, без привязки.
        await db.upsert_user(tg_user_id=tg_id, tg_username=tg_username)
        await message.answer(WELCOME_UNLINKED, parse_mode="Markdown")
    else:
        await message.answer(
            WELCOME_LINKED.format(username=linked_username),
            parse_mode="Markdown",
        )
