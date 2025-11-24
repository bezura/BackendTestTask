from typing import List

from pydantic import BaseModel


# ---- requests ----

# ---- inner DTO ----

class ReviewerAssignmentStats(BaseModel):
    user_id: str
    count: int


class AuthorPrStats(BaseModel):
    user_id: str
    count: int


class PrCountByStatus(BaseModel):
    OPEN: int
    MERGED: int


# ---- responses ----

class StatsResponse(BaseModel):
    assignments_per_reviewer: List[ReviewerAssignmentStats]
    open_prs_per_author: List[AuthorPrStats]
    merged_prs_per_author: List[AuthorPrStats]
    pr_count_by_status: PrCountByStatus
