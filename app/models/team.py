from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base


class Team(Base):
    __tablename__ = "teams"

    team_name: Mapped[str] = mapped_column(String, primary_key=True)

    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan"
    )


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_name", "user_id", name="uq_team_member"),
    )

    team_name: Mapped[str] = mapped_column(
        String,
        ForeignKey("teams.team_name", ondelete="CASCADE"),
        primary_key=True
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    user: Mapped["User"] = relationship("User", back_populates="teams")
    team: Mapped["Team"] = relationship("Team", back_populates="members")
