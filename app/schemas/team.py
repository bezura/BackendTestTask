from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.user import TeamMemberDTO


# ---- requests ----

class TeamAddRequest(BaseModel):
    team_name: str
    members: List[TeamMemberDTO]

class TeamGetRequest(BaseModel):
    team_name: str


class TeamDeactivateUsersRequest(BaseModel):
    team_name: str
    user_ids: Optional[List[str]] = None


# ---- inner DTO ----

class TeamDTO(BaseModel):
    team_name: str
    members: List[TeamMemberDTO]

    model_config = ConfigDict(from_attributes=True)


# ---- responses ----

class TeamAddResponse(BaseModel):
    team: TeamDTO
    model_config = ConfigDict(from_attributes=True)

class TeamGetResponse(BaseModel):
    team: TeamDTO
    model_config = ConfigDict(from_attributes=True)


class TeamDeactivateUsersResponse(BaseModel):
    team_name: str
    deactivated: List[str]
    reassigned_prs: int

    model_config = ConfigDict(from_attributes=True)
