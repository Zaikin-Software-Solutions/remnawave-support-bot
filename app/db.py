"""SQLite-слой бота.

Две сущности:
- users: маппинг tg_user_id ↔ remnawave_uuid (привязка через ?start=sub_<shortUuid>).
- message_links: связь "сообщение у владельца" → "сообщение у клиента". Нужна, чтобы
  Reply владельца на форварднутое сообщение находил адресата.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_user_id      INTEGER PRIMARY KEY,
    tg_username     TEXT,
    remnawave_uuid  TEXT,
    short_uuid      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS message_links (
    owner_msg_id    INTEGER PRIMARY KEY,
    client_tg_id    INTEGER NOT NULL,
    client_msg_id   INTEGER NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_message_links_client ON message_links(client_tg_id);
"""


@dataclass(slots=True)
class UserRecord:
    tg_user_id: int
    tg_username: Optional[str]
    remnawave_uuid: Optional[str]
    short_uuid: Optional[str]


@dataclass(slots=True)
class MessageLink:
    owner_msg_id: int
    client_tg_id: int
    client_msg_id: int


class Database:
    """Тонкая обёртка над aiosqlite. Один экземпляр на процесс."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        # Каталог под БД может ещё не существовать (при первом запуске в docker volume).
        Path(os.path.dirname(self._path) or ".").mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(_SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self._conn

    # ---------- users ----------

    async def upsert_user(
        self,
        *,
        tg_user_id: int,
        tg_username: Optional[str],
        remnawave_uuid: Optional[str] = None,
        short_uuid: Optional[str] = None,
    ) -> None:
        """Вставить или обновить пользователя. Не затирает существующий remnawave_uuid пустым."""
        await self.conn.execute(
            """
            INSERT INTO users (tg_user_id, tg_username, remnawave_uuid, short_uuid)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(tg_user_id) DO UPDATE SET
                tg_username = excluded.tg_username,
                remnawave_uuid = COALESCE(excluded.remnawave_uuid, users.remnawave_uuid),
                short_uuid     = COALESCE(excluded.short_uuid,     users.short_uuid),
                updated_at = datetime('now')
            """,
            (tg_user_id, tg_username, remnawave_uuid, short_uuid),
        )
        await self.conn.commit()

    async def get_user(self, tg_user_id: int) -> Optional[UserRecord]:
        async with self.conn.execute(
            "SELECT tg_user_id, tg_username, remnawave_uuid, short_uuid FROM users WHERE tg_user_id = ?",
            (tg_user_id,),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return UserRecord(
            tg_user_id=row["tg_user_id"],
            tg_username=row["tg_username"],
            remnawave_uuid=row["remnawave_uuid"],
            short_uuid=row["short_uuid"],
        )

    # ---------- message_links ----------

    async def save_link(self, *, owner_msg_id: int, client_tg_id: int, client_msg_id: int) -> None:
        await self.conn.execute(
            """
            INSERT OR REPLACE INTO message_links (owner_msg_id, client_tg_id, client_msg_id)
            VALUES (?, ?, ?)
            """,
            (owner_msg_id, client_tg_id, client_msg_id),
        )
        await self.conn.commit()

    async def find_client_by_owner_msg(self, owner_msg_id: int) -> Optional[MessageLink]:
        async with self.conn.execute(
            "SELECT owner_msg_id, client_tg_id, client_msg_id FROM message_links WHERE owner_msg_id = ?",
            (owner_msg_id,),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return MessageLink(
            owner_msg_id=row["owner_msg_id"],
            client_tg_id=row["client_tg_id"],
            client_msg_id=row["client_msg_id"],
        )
