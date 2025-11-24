import datetime
from datetime import timezone

from pydantic import ConfigDict, BaseModel, field_serializer

from app.schemas.schema_enums.pull_request_enums import PRStatus


# ---- requests ----

class PullRequestCreateRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str


class PullRequestReassignRequest(BaseModel):
    pull_request_id: str
    old_reviewer_id: str


class PullRequestMergeRequest(BaseModel):
    pull_request_id: str


# ---- inner DTO ----

class PullRequestShortDTO(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus

    model_config = ConfigDict(from_attributes=True)


class PullRequestDTO(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus
    assigned_reviewers: list[str]
    created_at: datetime.datetime | None = None
    merged_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "merged_at")
    def _ser_dt(self, v: datetime.datetime | None):
        if v is None:
            return None

        if v.tzinfo is None:
            local_tz = datetime.datetime.now().astimezone().tzinfo
            v = v.replace(tzinfo=local_tz)

        v = v.astimezone(timezone.utc)
        return v.isoformat().replace("+00:00", "Z")


# ---- responses ----

class PullRequestCreateResponse(BaseModel):
    pr: PullRequestDTO


class PullRequestReassignResponse(BaseModel):
    pr: PullRequestDTO
    replaced_by: str


class PullRequestMergeResponse(BaseModel):
    pr: PullRequestDTO
