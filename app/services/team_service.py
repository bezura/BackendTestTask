from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository
from app.schemas.team import TeamAddRequest, TeamDTO
from app.schemas.user import TeamMemberDTO
from app.models.team import Team
from app.utils.http_exceptions import http_error


class TeamService:

    async def create_or_update_team(self, db_session: AsyncSession, request: TeamAddRequest) -> TeamDTO:
        team_repo = TeamRepository(db_session=db_session)
        user_repo = UserRepository(db_session=db_session)

        member_by_id = {member.user_id: member for member in request.members}
        member_ids = set(member_by_id.keys())

        async with db_session.begin():
            team = await team_repo.get_by_name(request.team_name, with_relation=True)
            if not team:
                team = await team_repo.create_team(request.team_name)
            existing_member_ids = {member.user_id for member in team.members}

            for member in team.members:
                user = member.user
                payload = member_by_id.get(member.user_id)
                if payload:
                    user.username = payload.username
                    user.is_active = payload.is_active

            new_users_data = [
                {
                    "user_id": payload.user_id,
                    "username": payload.username,
                    "is_active": payload.is_active,
                }
                for user_id, payload in member_by_id.items()
                if user_id not in existing_member_ids
            ]
            await user_repo.create_many(new_users_data)

            removed_member_ids = list(existing_member_ids - member_ids)
            await team_repo.remove_members_by_user_ids(team.team_name, removed_member_ids)

            await team_repo.add_members_bulk(request.team_name, list(member_ids))

        team_with_members = await team_repo.get_by_name(request.team_name, with_relation=True)
        return self._build_team_dto(team_with_members)

    async def get_team(self, db: AsyncSession, team_name: str) -> TeamDTO:
        team_repo = TeamRepository(db)
        team = await team_repo.get_by_name(team_name, with_relation=True)
        if not team:
            http_error(404, "NOT_FOUND", "Team not found")
        return self._build_team_dto(team)

    def _build_team_dto(self, team: Team | None) -> TeamDTO:
        if team is None:
            http_error(404, "NOT_FOUND", "Team not found")
        members = []
        for member in team.members:
            user = member.user
            members.append(
                TeamMemberDTO(
                    user_id=member.user_id,
                    username=user.username if user else "",
                    is_active=user.is_active if user else True,
                )
            )
        return TeamDTO(team_name=team.team_name, members=members)
