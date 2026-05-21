"""Точка входа: запуск aiogram-бота в режиме long polling."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from .config import settings
from .db import Database
from .handlers import build_root_router
from .remnawave import RemnawaveClient


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("bot")

    db = Database(settings.db_path)
    await db.connect()

    remnawave = RemnawaveClient(
        base_url=settings.remnawave_base_url,
        api_token=settings.remnawave_api_token,
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=None),
    )
    dp = Dispatcher()
    dp.include_router(build_root_router())

    # Хендлеры достают зависимости из workflow_data через DI aiogram 3.
    logger.info("Starting bot, owner_tg_id=%s, panel=%s", settings.owner_tg_id, settings.remnawave_base_url)
    try:
        await dp.start_polling(bot, db=db, remnawave=remnawave)
    finally:
        await remnawave.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
