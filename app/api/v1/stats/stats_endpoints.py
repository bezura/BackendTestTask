import logging

from fastapi import APIRouter

from app.api.dependencies import DBSession
from app.schemas.stats import StatsResponse
from app.services.stats_service import StatsService

router = APIRouter()
logger = logging.getLogger(__name__)
service = StatsService()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db_session: DBSession):
    return await service.get_stats(db_session)
