from pydantic import BaseModel, ConfigDict
from typing import List

from app.schemas.pull_request import PullRequestShortDTO


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


class UserSetIsActiveRequest(BaseModel):
    user_id: str
    is_active: bool


class UserSetIsActiveResponse(BaseModel):
    user: UserDTO


class UserReviewsResponse(BaseModel):
    user_id: str
    pull_requests: List[PullRequestShortDTO]
