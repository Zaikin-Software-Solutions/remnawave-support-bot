from aiogram import Router

from .start import router as start_router
from .owner import router as owner_router
from .client import router as client_router


def build_root_router() -> Router:
    """Собирает все routers в нужном порядке.

    Порядок важен: owner_router должен идти раньше client_router, иначе сообщение
    владельца в личке боту попадёт в client_router как "сообщение от клиента".
    """
    root = Router()
    root.include_router(start_router)
    root.include_router(owner_router)
    root.include_router(client_router)
    return root


__all__ = ["build_root_router"]
