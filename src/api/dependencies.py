from functools import lru_cache

from src.repositories.session_repository import InMemorySessionRepository
from src.services.session_service import SessionService


@lru_cache
def get_session_repository() -> InMemorySessionRepository:
    return InMemorySessionRepository()


def get_session_service() -> SessionService:
    return SessionService(get_session_repository())
