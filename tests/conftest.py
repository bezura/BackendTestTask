import os

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.dependencies import get_session
from app.core.config import settings
from app.core.db import Base
from app.main import app

DATABASE_URL = settings.postgres_async_url
TEST_SCHEMA = os.getenv("TEST_SCHEMA", "test")

if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL for tests")


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(DATABASE_URL, future=True)

    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{TEST_SCHEMA}"'))
        await conn.execute(text(f'SET search_path TO "{TEST_SCHEMA}"'))

        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_db(engine):
    async with engine.begin() as conn:
        await conn.execute(text(f'SET search_path TO "{TEST_SCHEMA}"'))

        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client(engine):
    session_local = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
        autoflush=False,
    )

    async def _override_get_session():
        async with session_local() as session:
            await session.execute(text(f'SET search_path TO "{TEST_SCHEMA}"'))
            await session.commit()
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()
