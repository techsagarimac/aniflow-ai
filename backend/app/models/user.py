from __future__ import annotations

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ArtistRole, Availability, ExperienceLevel, UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    avatar_color: Mapped[str] = mapped_column(String(16), default="#7C9CFF")

    artist_profile: Mapped[ArtistProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    assigned_scenes: Mapped[list["Scene"]] = relationship(
        back_populates="assigned_artist", foreign_keys="Scene.assigned_artist_id"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        back_populates="assignee", foreign_keys="Task.assignee_id"
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")


class ArtistProfile(Base, TimestampMixin):
    __tablename__ = "artist_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    artist_role: Mapped[ArtistRole] = mapped_column(Enum(ArtistRole), nullable=False)
    skills: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    experience_level: Mapped[ExperienceLevel] = mapped_column(
        Enum(ExperienceLevel), default=ExperienceLevel.MID
    )
    availability: Mapped[Availability] = mapped_column(
        Enum(Availability), default=Availability.AVAILABLE
    )
    avg_completion_hours: Mapped[float] = mapped_column(default=8.0)

    user: Mapped[User] = relationship(back_populates="artist_profile")
