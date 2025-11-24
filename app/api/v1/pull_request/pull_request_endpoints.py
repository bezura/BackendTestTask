import logging

from fastapi import APIRouter

from app.api.dependencies import DBSession
from app.schemas.pull_request import PullRequestCreateRequest, PullRequestCreateResponse
from app.services.pr_service import PRService


router = APIRouter()
logger = logging.getLogger(__name__)
service = PRService()


@router.post(
    "/create",
    response_model=PullRequestCreateResponse,
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
