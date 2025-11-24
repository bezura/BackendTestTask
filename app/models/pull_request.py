from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, int_pk
from app.schemas.schema_enums.pull_request_enums import PRStatus

if TYPE_CHECKING:
    from .user import User


class PullRequest(Base):
    __tablename__ = "pull_requests"

    pull_request_id: Mapped[str] = mapped_column(String, primary_key=True)
    pull_request_name: Mapped[str] = mapped_column(String, nullable=False)

    author_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[PRStatus] = mapped_column(
        Enum(PRStatus, name="pr_status"), default=PRStatus.OPEN, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    author: Mapped[User] = relationship("User", back_populates="pr_authored")

    reviewers: Mapped[list[PRReviewer]] = relationship(
        "PRReviewer", back_populates="pull_request", cascade="all, delete-orphan"
    )


class PRReviewer(Base):
    __tablename__ = "pr_reviewers"
    __table_args__ = (UniqueConstraint("pull_request_id", "reviewer_id", name="uq_pr_reviewer"),)

    id: Mapped[int_pk]
    pull_request_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("pull_requests.pull_request_id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    pull_request: Mapped[PullRequest] = relationship("PullRequest", back_populates="reviewers")
