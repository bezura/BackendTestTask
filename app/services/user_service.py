from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pull_request_repo import PullRequestRepository
from app.repositories.user_repo import UserRepository
from app.schemas.pull_request import PullRequestShortDTO
from app.schemas.user import (
    UserSetIsActiveRequest,
    UserSetIsActiveResponse,
    UserReviewsResponse,
    UserDTO,
)
from app.utils.http_exceptions import http_error


class UserService:
    async def set_active(self, db_session: AsyncSession, payload: UserSetIsActiveRequest) -> UserSetIsActiveResponse:
        repo = UserRepository(db_session)
        async with db_session.begin():
            user = await repo.get_with_team(payload.user_id)
            if not user:
                http_error(404, "NOT_FOUND", "User not found")
            user.is_active = payload.is_active
        response = UserSetIsActiveResponse(user=self._build_user_dto(user))
        return response

    async def get_reviews(self, db_session: AsyncSession, user_id: str) -> UserReviewsResponse:
        user_repo = UserRepository(db_session)
        pr_repo = PullRequestRepository(db_session)
        user = await user_repo.get_with_team(user_id)
        if not user:
            http_error(404, "NOT_FOUND", "User not found")
        prs = await pr_repo.get_review_assignments(user_id)
        return UserReviewsResponse(
            user_id=user_id,
            pull_requests=[self._build_pull_request_short_dto(pr) for pr in prs],
        )

    def _build_user_dto(self, user) -> UserDTO:
        team_name = user.teams[0].team_name if user.teams else ""
        return UserDTO(
            user_id=user.user_id,
            username=user.username,
            team_name=team_name,
            is_active=user.is_active,
        )

    def _build_pull_request_short_dto(self, pr) -> PullRequestShortDTO:
        return PullRequestShortDTO(
            pull_request_id=pr.pull_request_id,
            pull_request_name=pr.pull_request_name,
            author_id=pr.author_id,
            status=pr.status,
        )
