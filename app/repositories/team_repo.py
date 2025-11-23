from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import Team, TeamMember


class TeamRepository:
    def __init__(self, db_session: AsyncSession):
        self._db_session = db_session

    async def get_by_name(self, team_name: str, with_relation: bool = False) -> Team | None:
        stmt = select(Team).where(Team.team_name == team_name)
        if with_relation:
            stmt = stmt.options(
                selectinload(Team.members).selectinload(TeamMember.user)
            )
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_team(self, team_name: str) -> Team:
        team = Team(team_name=team_name)
        self._db_session.add(team)
        return team

    async def add_member(self, team_name: str, user_id: str) -> TeamMember | None:
        stmt = select(TeamMember).where(
            TeamMember.team_name == team_name,
            TeamMember.user_id == user_id
        )
        exists = await self._db_session.execute(stmt)
        if exists.scalar_one_or_none():
            return None
        member = TeamMember(team_name=team_name, user_id=user_id)
        self._db_session.add(member)
        return member

    async def add_members_bulk(self, team_name: str, user_ids: list[str]) -> None:
        if not user_ids:
            return
        stmt = select(TeamMember.user_id).where(
            TeamMember.team_name == team_name,
            TeamMember.user_id.in_(user_ids)
        )
        existing = await self._db_session.execute(stmt)
        existing_ids = {row[0] for row in existing.all()}
        new_members = [
            TeamMember(team_name=team_name, user_id=user_id)
            for user_id in user_ids
            if user_id not in existing_ids
        ]
        self._db_session.add_all(new_members)

    async def remove_members_by_user_ids(self, team_name: str, user_ids: list[str]) -> None:
        if not user_ids:
            return
        stmt = delete(TeamMember).where(
            TeamMember.team_name == team_name,
            TeamMember.user_id.in_(user_ids),
        )
        await self._db_session.execute(stmt)
