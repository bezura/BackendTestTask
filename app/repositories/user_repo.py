import logging
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.team import TeamMember

logger = logging.getLogger(__name__)


class UserRepository:

    def __init__(self, db_session: AsyncSession):
        self._db_session = db_session

    async def get_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.user_id == user_id)
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_team(self, user_id: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.teams).selectinload(TeamMember.team))
            .where(User.user_id == user_id)
        )
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

    async def get_active_review_candidates_for_author(self, author: User) -> set[str]:
        """Вернуть множество user_id активных кандидатов в ревьюверы для автора.

        Кандидаты — все активные пользователи из команд автора (включая самого автора;
        исключение автора делается на уровне сервисного слоя).
        Если у автора нет команд, возвращаем пустое множество — сервис сам решит,
        считать ли это ошибкой или ситуацией без ревьюверов.
        """
        if not author.teams:
            return set()

        team_names = [member.team_name for member in author.teams]
        if not team_names:
            return set()

        stmt = (
            select(TeamMember)
            .join(User, TeamMember.user_id == User.user_id)
            .where(
                TeamMember.team_name.in_(team_names),
                User.is_active.is_(True),
            )
        )
        result = await self._db_session.execute(stmt)
        members = result.scalars().all()
        return {member.user_id for member in members}
