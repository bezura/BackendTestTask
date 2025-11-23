from pydantic import BaseModel, ConfigDict


class TeamMemberDTO(BaseModel):
    user_id: str
    username: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
