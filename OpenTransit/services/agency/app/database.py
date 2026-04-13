"""Database session management for the agency service."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

_engine = None
_AsyncSessionLocal = None


def get_engine():
    global _engine, _AsyncSessionLocal
    if _engine is None:
        _engine = create_async_engine(settings.database_url, echo=False, future=True)
        _AsyncSessionLocal = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    get_engine()
    async with _AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
