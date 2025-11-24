import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.repositories.pull_request_repo import PullRequestRepository
from app.repositories.team_repo import TeamRepository
from app.repositories.user_repo import UserRepository
from app.schemas.team import TeamAddRequest, TeamDTO, TeamDeactivateUsersRequest, TeamDeactivateUsersResponse
from app.schemas.user import TeamMemberDTO
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
            await db_session.flush()
        db_session.expire_all()

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

    async def deactivate_users_and_reassign_prs(
            self,
            db_session: AsyncSession,
            payload: TeamDeactivateUsersRequest,
    ) -> TeamDeactivateUsersResponse:
        team_repo = TeamRepository(db_session)
        user_repo = UserRepository(db_session)
        pr_repo = PullRequestRepository(db_session)

        async with db_session.begin():
            team = await team_repo.get_by_name(payload.team_name, with_relation=False)
            if not team:
                http_error(404, "NOT_FOUND", "Team not found")

            team_member_ids = await user_repo.get_team_member_ids(payload.team_name)
            if not team_member_ids:
                # команда есть, но пуста
                return TeamDeactivateUsersResponse(
                    team_name=payload.team_name,
                    deactivated=[],
                    reassigned_prs=0,
                )

            target_ids = set(team_member_ids if payload.user_ids is None else payload.user_ids)
            target_ids &= set(team_member_ids)  # нельзя деактивировать не-члена команды

            if not target_ids:
                return TeamDeactivateUsersResponse(
                    team_name=payload.team_name,
                    deactivated=[],
                    reassigned_prs=0,
                )

            await user_repo.deactivate_users(list(target_ids))

            prs = await pr_repo.get_open_prs_with_reviewers(list(target_ids))

            inactive_users = await user_repo.get_users_with_teams(list(target_ids))
            inactive_by_id = {u.user_id: u for u in inactive_users}

            reassigned = 0

            for pr in prs:
                current_reviewers = {r.reviewer_id for r in pr.reviewers}
                inactive_here = current_reviewers & target_ids
                if not inactive_here:
                    continue

                for old_id in list(inactive_here):
                    old_user = inactive_by_id.get(old_id)
                    if not old_user:
                        await pr_repo.remove_reviewer(pr.pull_request_id, old_id)
                        current_reviewers.discard(old_id)
                        continue

                    candidate_ids = await user_repo.get_active_review_candidates_for_author(old_user)

                    forbidden = {pr.author_id, old_id} | (current_reviewers - {old_id})
                    candidate_ids = {cid for cid in candidate_ids if cid not in forbidden}

                    if not candidate_ids:
                        await pr_repo.remove_reviewer(pr.pull_request_id, old_id)
                        current_reviewers.discard(old_id)
                        continue

                    new_id = random.choice(list(candidate_ids))
                    await pr_repo.replace_reviewer(pr, old_id, new_id)
                    current_reviewers.discard(old_id)
                    current_reviewers.add(new_id)
                    reassigned += 1

        return TeamDeactivateUsersResponse(
            team_name=payload.team_name,
            deactivated=list(target_ids),
            reassigned_prs=reassigned,
        )
