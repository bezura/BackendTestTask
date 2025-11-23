from typing import List
from pydantic import BaseModel, ConfigDict
from app.schemas.user import TeamMemberDTO

# ---- requests ----

class TeamAddRequest(BaseModel):
    team_name: str
    members: List[TeamMemberDTO]

class TeamGetRequest(BaseModel):
    team_name: str


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
