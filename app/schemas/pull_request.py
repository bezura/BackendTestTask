import datetime

from pydantic import ConfigDict, BaseModel

from app.schemas.schema_enums.pull_request_enums import PRStatus

class PullRequestCreateRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str

class PullRequestDTO(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus
    assigned_reviewers: list[str]
    created_at: datetime.datetime | None = None
    merged_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PullRequestCreateResponse(BaseModel):
    pr: PullRequestDTO


class PullRequestShortDTO(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus

    model_config = ConfigDict(from_attributes=True)
