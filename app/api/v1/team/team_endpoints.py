import logging

from fastapi import APIRouter

from app.api.dependencies import DBSession
from app.schemas.team import (
    TeamAddRequest,
    TeamAddResponse,
    TeamGetResponse, TeamDeactivateUsersResponse, TeamDeactivateUsersRequest
)
from app.services.team_service import TeamService

router = APIRouter()
logger = logging.getLogger(__name__)
service = TeamService()


@router.post(
    "/add",
    response_model=TeamAddResponse,
    status_code=201
)
async def add_team(
        request: TeamAddRequest,
        db_session: DBSession,
):
    team = await service.create_or_update_team(db_session, request)
    return TeamAddResponse(team=team)


@router.get(
    "/get",
    response_model=TeamGetResponse,
)
async def get_team(
        team_name: str,
        db_session: DBSession,
):
    team = await service.get_team(db_session, team_name)
    return TeamGetResponse(team=team)


@router.post(
    "/deactivateUsers",
    response_model=TeamDeactivateUsersResponse
)
async def deactivate_users(
        payload: TeamDeactivateUsersRequest,
        db: DBSession,
):
    return await service.deactivate_users_and_reassign_prs(db, payload)
