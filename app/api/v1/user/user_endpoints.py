import logging

from fastapi import APIRouter

from app.api.dependencies import DBSession
from app.schemas.user import (
    UserReviewsResponse,
    UserSetIsActiveRequest,
    UserSetIsActiveResponse,
)
from app.services.user_service import UserService

router = APIRouter()
logger = logging.getLogger(__name__)
service = UserService()


@router.post("/setIsActive", response_model=UserSetIsActiveResponse)
async def set_is_active(request: UserSetIsActiveRequest, db_session: DBSession):
    return await service.set_active(db_session, request)


@router.get("/getReview", response_model=UserReviewsResponse)
async def get_review(user_id: str, db_session: DBSession):
    return await service.get_reviews(db_session, user_id)
