from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stats_repo import StatsRepository
from app.schemas.schema_enums.pull_request_enums import PRStatus
from app.schemas.stats import (
    StatsResponse,
    ReviewerAssignmentStats,
    AuthorPrStats,
    PrCountByStatus,
)


class StatsService:
    async def get_stats(self, db_session: AsyncSession) -> StatsResponse:
        repo = StatsRepository(db_session)

        assignments = await repo.get_assignments_per_reviewer()
        open_prs = await repo.get_open_prs_per_author()
        merged_prs = await repo.get_merged_prs_per_author()
        status_counts = await repo.get_pr_count_by_status()
        return StatsResponse(
            assignments_per_reviewer=[
                ReviewerAssignmentStats(user_id=user_id, count=count)
                for user_id, count in assignments
            ],
            open_prs_per_author=[
                AuthorPrStats(user_id=user_id, count=count)
                for user_id, count in open_prs
            ],
            merged_prs_per_author=[
                AuthorPrStats(user_id=user_id, count=count)
                for user_id, count in merged_prs
            ],
            pr_count_by_status=PrCountByStatus(
                OPEN=status_counts.get(PRStatus.OPEN, 0),
                MERGED=status_counts.get(PRStatus.OPEN, 0),
            ),
        )
