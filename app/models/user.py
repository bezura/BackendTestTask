from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    teams: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="user", cascade="all, delete-orphan"
    )

    pr_authored: Mapped[list["PullRequest"]] = relationship(
        "PullRequest", back_populates="author"
    )
