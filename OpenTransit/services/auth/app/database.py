"""Database session management for the auth service."""

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


# Expose engine for use in main.py startup
@property
def engine():
    return get_engine()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    get_engine()
    async with _AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
