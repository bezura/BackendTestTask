from pydantic import BaseModel, ConfigDict

from app.schemas.pull_request import PullRequestShortDTO

# ---- requests ----


class UserSetIsActiveRequest(BaseModel):
    user_id: str
    is_active: bool


# ---- inner DTO ----


class TeamMemberDTO(BaseModel):
    user_id: str
    username: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserDTO(BaseModel):
    user_id: str
    username: str
    team_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ---- responses ----


class UserSetIsActiveResponse(BaseModel):
    user: UserDTO


class UserReviewsResponse(BaseModel):
    user_id: str
    pull_requests: list[PullRequestShortDTO]
