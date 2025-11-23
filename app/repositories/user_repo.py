import logging
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:

    def __init__(self, db_session: AsyncSession):
        self._db_session = db_session

    async def get_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.user_id == user_id)
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, user_ids: Iterable[str]) -> list[User]:
        ids = list(user_ids)
        if not ids:
            return []
        stmt = select(User).where(User.user_id.in_(ids))
        result = await self._db_session.execute(stmt)
        return list(result.scalars())

    async def create_many(self, users_data: list[dict]) -> list[User]:
        if not users_data:
            return []
        users = [
            User(
                user_id=data["user_id"],
                username=data["username"],
                is_active=data["is_active"],
            )
            for data in users_data
        ]
        self._db_session.add_all(users)
        return users
