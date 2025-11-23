import datetime
from typing import Annotated

from sqlalchemy import BigInteger, text, ARRAY, Integer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, mapped_column

from app.core.config import settings

async_engine = create_async_engine(settings.postgres_async_url, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)

int_pk = Annotated[int, mapped_column(BigInteger, primary_key=True, autoincrement=True)]

created_at = Annotated[
    datetime.datetime,
    mapped_column(server_default=text("TIMEZONE('utc', now())"), nullable=False)
]
class Base(DeclarativeBase):
    repr_cols_num: int = 3
    repr_cols: tuple = ()

    type_annotation_map = {
        list[int]: ARRAY(Integer)
    }

    def __repr__(self) -> str:
        cols = [
            f"{col}={getattr(self, col)}"
            for idx, col in enumerate(self.__table__.columns.keys())
            if col in self.repr_cols or idx < self.repr_cols_num
        ]
        return f"<{self.__class__.__name__} {', '.join(cols)}>"