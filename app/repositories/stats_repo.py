from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pull_request import PRReviewer, PullRequest


class StatsRepository:
    def __init__(self, db_session: AsyncSession):
        self._db_session = db_session

    async def get_assignments_per_reviewer(self) -> list[tuple[str, int]]:
        stmt = select(PRReviewer.reviewer_id, func.count()).group_by(PRReviewer.reviewer_id)
        result = await self._db_session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_open_prs_per_author(self) -> list[tuple[str, int]]:
        stmt = (
            select(PullRequest.author_id, func.count())
            .where(PullRequest.status == "OPEN")
            .group_by(PullRequest.author_id)
        )
        result = await self._db_session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_merged_prs_per_author(self) -> list[tuple[str, int]]:
        stmt = (
            select(PullRequest.author_id, func.count())
            .where(PullRequest.status == "MERGED")
            .group_by(PullRequest.author_id)
        )
        result = await self._db_session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_pr_count_by_status(self) -> dict[str, int]:
        stmt = select(PullRequest.status, func.count()).group_by(PullRequest.status)
        result = await self._db_session.execute(stmt)
        rows = result.all()
        return {row[0]: row[1] for row in rows}
