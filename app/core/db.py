from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

async_engine = create_async_engine(settings.postgres_async_url, pool_pre_ping=True)
