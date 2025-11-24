from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pull_request import PullRequest, PRReviewer


class PullRequestRepository:
    def __init__(self, db_session: AsyncSession):
        self._db_session = db_session

    async def get_by_id(self, pull_request_id: str, with_reviewers: bool = False) -> PullRequest | None:
        stmt = select(PullRequest).where(PullRequest.pull_request_id == pull_request_id)
        if with_reviewers:
            stmt = stmt.options(selectinload(PullRequest.reviewers).selectinload(PRReviewer.pull_request))
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, pr: PullRequest) -> PullRequest:
        self._db_session.add(pr)
        return pr

    async def assign_reviewers(self, pr: PullRequest, reviewer_ids: list[str]) -> None:
        existing = {reviewer.reviewer_id for reviewer in pr.reviewers}
        new_reviewers = [
            PRReviewer(pull_request_id=pr.pull_request_id, reviewer_id=reviewer_id)
            for reviewer_id in reviewer_ids
            if reviewer_id not in existing
        ]
        self._db_session.add_all(new_reviewers)

    async def get_review_assignments(self, user_id: str) -> list[PullRequest]:
        stmt = (
            select(PullRequest)
            .join(PRReviewer)
            .where(PRReviewer.reviewer_id == user_id)
        )
        result = await self._db_session.execute(stmt)
        return list(result.scalars())

    async def get_for_update(self, pull_request_id: str) -> PullRequest | None:
        stmt = (
            select(PullRequest)
            .where(PullRequest.pull_request_id == pull_request_id)
            .with_for_update()
            .options(selectinload(PullRequest.reviewers))
        )
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def replace_reviewer(self, pr: PullRequest, old_reviewer_id: str, new_user_id: str) -> None:
        pr.reviewers = [r for r in pr.reviewers if r.reviewer_id != old_reviewer_id]

        existing_ids = {r.reviewer_id for r in pr.reviewers}
        if new_user_id in existing_ids:
            return

        new_reviewer = PRReviewer(
            pull_request_id=pr.pull_request_id,
            reviewer_id=new_user_id,
        )
        self._db_session.add(new_reviewer)
