"""HTTP-клиент к Remnawave Panel API (v2.7).

Используем только то, что нужно боту:
- найти пользователя по shortUuid (deep-link с sub-страницы);
- найти пользователя свободным поиском (когда клиент пришёл "мимо" deep-link);
- отдать карточку с актуальным статусом подписки.

API: GET /api/users/by-short-uuid/{shortUuid}
     GET /api/users/{uuid}
     GET /api/users/resolve?query=...
Аутентификация: Bearer <REMNAWAVE_API_TOKEN>.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RemnawaveUser:
    """Срез полей пользователя Remnawave, нужный боту."""

    uuid: str
    short_uuid: str
    username: str
    status: str  # ACTIVE / DISABLED / LIMITED / EXPIRED
    expire_at: Optional[datetime]
    traffic_limit_bytes: int  # 0 = unlimited
    used_traffic_bytes: int
    telegram_id: Optional[int]
    subscription_url: Optional[str]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "RemnawaveUser":
        expire_raw = data.get("expireAt")
        expire_at: Optional[datetime] = None
        if expire_raw:
            # API отдаёт ISO 8601 с 'Z' — нормализуем под fromisoformat.
            expire_at = datetime.fromisoformat(expire_raw.replace("Z", "+00:00"))

        traffic = data.get("userTraffic") or {}
        return cls(
            uuid=data["uuid"],
            short_uuid=data.get("shortUuid", ""),
            username=data.get("username", ""),
            status=data.get("status", "UNKNOWN"),
            expire_at=expire_at,
            traffic_limit_bytes=int(data.get("trafficLimitBytes", 0) or 0),
            used_traffic_bytes=int(traffic.get("usedTrafficBytes", 0) or 0),
            telegram_id=data.get("telegramId"),
            subscription_url=data.get("subscriptionUrl"),
        )

    # ---------- человекочитаемые поля для caption ----------

    @property
    def expire_human(self) -> str:
        if self.expire_at is None:
            return "—"
        now = datetime.now(timezone.utc)
        days_left = (self.expire_at - now).days
        date_str = self.expire_at.strftime("%Y-%m-%d")
        # > 50 лет — это синтетический "вечный" аккаунт, не показываем "осталось".
        if days_left > 365 * 50:
            return f"{date_str} (бессрочно)"
        if days_left < 0:
            return f"{date_str} (истёк {-days_left} дн. назад)"
        return f"{date_str} (осталось {days_left} дн.)"

    @property
    def traffic_human(self) -> str:
        used_gb = self.used_traffic_bytes / 1024 / 1024 / 1024
        if self.traffic_limit_bytes == 0:
            return f"{used_gb:.2f} GB / ∞"
        limit_gb = self.traffic_limit_bytes / 1024 / 1024 / 1024
        return f"{used_gb:.2f} / {limit_gb:.2f} GB"


class RemnawaveClient:
    """Тонкий async-клиент к API панели. Один экземпляр на процесс."""

    def __init__(self, base_url: str, api_token: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_user_by_short_uuid(self, short_uuid: str) -> Optional[RemnawaveUser]:
        return await self._get_user(f"/api/users/by-short-uuid/{short_uuid}")

    async def get_user_by_uuid(self, uuid: str) -> Optional[RemnawaveUser]:
        return await self._get_user(f"/api/users/{uuid}")

    async def resolve(self, query: str) -> Optional[RemnawaveUser]:
        """Поиск по произвольному запросу (username / email / tg_id).
        Возвращает первого подходящего, иначе None.
        """
        try:
            resp = await self._client.get("/api/users/resolve", params={"query": query})
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.warning("Remnawave resolve(%s) failed: %s", query, e)
            return None
        except httpx.HTTPError as e:
            logger.warning("Remnawave resolve(%s) transport error: %s", query, e)
            return None

        payload = resp.json().get("response") or {}
        # API может вернуть либо одного пользователя, либо список.
        if isinstance(payload, list):
            users = payload
        else:
            users = payload.get("users") if isinstance(payload, dict) else None
            if users is None and isinstance(payload, dict) and "uuid" in payload:
                users = [payload]

        if not users:
            return None
        return RemnawaveUser.from_api(users[0])

    # ---------- private ----------

    async def _get_user(self, path: str) -> Optional[RemnawaveUser]:
        try:
            resp = await self._client.get(path)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.warning("Remnawave GET %s failed: %s", path, e)
            return None
        except httpx.HTTPError as e:
            logger.warning("Remnawave GET %s transport error: %s", path, e)
            return None

        data = resp.json().get("response")
        if not data:
            return None
        return RemnawaveUser.from_api(data)
