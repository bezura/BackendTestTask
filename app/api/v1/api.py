from fastapi import APIRouter
from app.api.v1.health import health_endpoints
from app.api.v1.team import team_endpoints
from app.api.v1.user import user_endpoints
from app.api.v1.pull_request import pull_request_endpoints

api_router = APIRouter()

api_router.include_router(
    health_endpoints.router, tags=["health"]
)

api_router.include_router(
    team_endpoints.router, prefix="/team", tags=["team"]
)

api_router.include_router(
    user_endpoints.router, prefix="/users", tags=["users"]
)

api_router.include_router(
    pull_request_endpoints.router, prefix="/pullRequest", tags=["PullRequests"]
)
