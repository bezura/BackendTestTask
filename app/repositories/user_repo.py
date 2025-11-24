import logging
from collections.abc import Iterable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import TeamMember
from app.models.user import User

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
        """
        Candidates — all active users from author's teams. If author has no teams, return empty set.
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

    async def get_team_member_ids(self, team_name: str) -> list[str]:
        stmt = select(TeamMember.user_id).where(TeamMember.team_name == team_name)
        res = await self._db_session.execute(stmt)
        return list(res.scalars().all())

    async def deactivate_users(self, user_ids: list[str]) -> int:
        if not user_ids:
            return 0
        stmt = update(User).where(User.user_id.in_(user_ids)).values(is_active=False)
        res = await self._db_session.execute(stmt)
        return res.rowcount or 0  # type: ignore[attr-defined]

    async def get_users_with_teams(self, user_ids: list[str]) -> list[User]:
        if not user_ids:
            return []
        stmt = select(User).where(User.user_id.in_(user_ids)).options(selectinload(User.teams))
        res = await self._db_session.execute(stmt)
        return list(res.scalars().all())
