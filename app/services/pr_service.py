from __future__ import annotations

import random
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pull_request import PullRequest
from app.repositories.pull_request_repo import PullRequestRepository
from app.repositories.user_repo import UserRepository
from app.schemas.pull_request import PullRequestDTO
from app.schemas.schema_enums.pull_request_enums import PRStatus
from app.utils.http_exceptions import http_error


class PRService:
    async def create_pr(
        self,
        db_session: AsyncSession,
        pull_request_id: str,
        pull_request_name: str,
        author_id: str,
    ) -> PullRequestDTO:
        pr_repo = PullRequestRepository(db_session)
        user_repo = UserRepository(db_session)

        async with db_session.begin():
            existing = await pr_repo.get_by_id(pull_request_id, with_reviewers=True)
            if existing:
                http_error(409, "PR_EXISTS", "PR id already exists")

            author = await user_repo.get_with_team(author_id)
            if not author:
                http_error(404, "NOT_FOUND", "Author not found")

            candidate_ids = await user_repo.get_active_review_candidates_for_author(author)
            if not author.teams or not candidate_ids:
                http_error(404, "NOT_FOUND", "Author team not found")

            reviewer_ids = self._choose_reviewers(candidate_ids, author_id)

            pr = PullRequest(
                pull_request_id=pull_request_id,
                pull_request_name=pull_request_name,
                author_id=author_id,
                status=PRStatus.OPEN,
            )
            await pr_repo.create(pr)
            if reviewer_ids:
                await pr_repo.assign_reviewers(pr, reviewer_ids)
            await db_session.flush()
        db_session.expire_all()

        created_pr = await pr_repo.get_by_id(pull_request_id, with_reviewers=True)
        if not created_pr:
            http_error(500, "NOT_FOUND", "PR not found after creation")

        return self._build_pr_dto(created_pr)

    async def merge_pr(
        self,
        db_session: AsyncSession,
        pull_request_id: str,
    ) -> PullRequestDTO:
        pr_repo = PullRequestRepository(db_session)

        async with db_session.begin():
            pr = await pr_repo.get_for_update(pull_request_id)
            if not pr:
                http_error(404, "NOT_FOUND", "PR not found")

            if pr.status != PRStatus.MERGED:
                pr.status = PRStatus.MERGED
                pr.merged_at = datetime.now(UTC)

        merged_pr = await pr_repo.get_by_id(pull_request_id, with_reviewers=True)
        if not merged_pr:
            http_error(500, "NOT_FOUND", "PR not found after merge")

        return self._build_pr_dto(merged_pr)

    async def reassign_reviewer(
        self,
        db_session: AsyncSession,
        pull_request_id: str,
        old_reviewer_id: str,
    ) -> tuple[PullRequestDTO, str]:
        pr_repo = PullRequestRepository(db_session)
        user_repo = UserRepository(db_session)

        async with db_session.begin():
            pr = await pr_repo.get_for_update(pull_request_id)
            if not pr:
                http_error(404, "NOT_FOUND", "PR not found")

            if pr.status == PRStatus.MERGED:
                http_error(409, "PR_MERGED", "cannot reassign on merged PR")

            current_reviewer_ids = {r.reviewer_id for r in pr.reviewers}
            if old_reviewer_id not in current_reviewer_ids:
                http_error(409, "NOT_ASSIGNED", "reviewer is not assigned to this PR")

            old_user = await user_repo.get_with_team(old_reviewer_id)
            if not old_user:
                http_error(404, "NOT_FOUND", "Reviewer user not found")

            candidate_ids = await user_repo.get_active_review_candidates_for_author(old_user)

            other_reviewer_ids = current_reviewer_ids - {old_reviewer_id}
            forbidden_ids = {pr.author_id, old_reviewer_id} | other_reviewer_ids
            candidate_ids = {uid for uid in candidate_ids if uid not in forbidden_ids}

            if not candidate_ids:
                http_error(409, "NO_CANDIDATE", "no active replacement candidate in team")

            new_reviewer_id = self._choose_replacement_reviewer(candidate_ids)

            await pr_repo.replace_reviewer(
                pr, old_reviewer_id=old_reviewer_id, new_user_id=new_reviewer_id
            )
            await db_session.flush()
        db_session.expire_all()
        updated_pr = await pr_repo.get_by_id(pull_request_id, with_reviewers=True)
        if not updated_pr:
            http_error(500, "NOT_FOUND", "PR not found after reassign")

        return self._build_pr_dto(updated_pr), new_reviewer_id

    def _choose_replacement_reviewer(self, candidate_ids: set[str]) -> str:
        return random.choice(list(candidate_ids))

    def _choose_reviewers(self, candidate_ids: set[str], author_id: str) -> list[str]:
        candidate_ids = {uid for uid in candidate_ids if uid != author_id}

        if not candidate_ids:
            return []
        if len(candidate_ids) == 1:
            return list(candidate_ids)
        return random.sample(list(candidate_ids), k=2)

    def _build_pr_dto(self, pr: PullRequest) -> PullRequestDTO:
        assigned_reviewers = [rev.reviewer_id for rev in pr.reviewers]
        return PullRequestDTO(
            pull_request_id=pr.pull_request_id,
            pull_request_name=pr.pull_request_name,
            author_id=pr.author_id,
            status=pr.status,
            assigned_reviewers=assigned_reviewers,
            created_at=pr.created_at,
            merged_at=pr.merged_at,
        )
