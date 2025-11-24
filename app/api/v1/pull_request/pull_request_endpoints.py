import logging

from fastapi import APIRouter

from app.api.dependencies import DBSession
from app.schemas.pull_request import (
    PullRequestCreateRequest,
    PullRequestCreateResponse,
    PullRequestReassignRequest,
    PullRequestReassignResponse,
    PullRequestMergeRequest,
    PullRequestMergeResponse,
)
from app.services.pr_service import PRService

router = APIRouter()
logger = logging.getLogger(__name__)
service = PRService()


@router.post(
    "/create",
    response_model=PullRequestCreateResponse,
    status_code=201
)
async def create_pull_request(
        request: PullRequestCreateRequest,
        db_session: DBSession,
):
    pr = await service.create_pr(
        db_session=db_session,
        pull_request_id=request.pull_request_id,
        pull_request_name=request.pull_request_name,
        author_id=request.author_id,
    )
    return PullRequestCreateResponse(pr=pr)


@router.post(
    "/reassign",
    response_model=PullRequestReassignResponse,
)
async def reassign_reviewer(
        request: PullRequestReassignRequest,
        db_session: DBSession,
):
    pr_dto, replaced_by = await service.reassign_reviewer(
        db_session=db_session,
        pull_request_id=request.pull_request_id,
        old_reviewer_id=request.old_reviewer_id,
    )
    return PullRequestReassignResponse(pr=pr_dto, replaced_by=replaced_by)


@router.post(
    "/merge",
    response_model=PullRequestMergeResponse,
)
async def merge_pull_request(
        request: PullRequestMergeRequest,
        db_session: DBSession,
):
    pr_dto = await service.merge_pr(
        db_session=db_session,
        pull_request_id=request.pull_request_id,
    )
    return PullRequestMergeResponse(pr=pr_dto)
