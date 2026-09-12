from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Table, Text, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import (
    EpisodeStatus,
    KanbanColumn,
    Priority,
    ProductionStage,
    ProjectStatus,
    SceneStatus,
    STAGE_TO_KANBAN,
)

scene_characters = Table(
    "scene_characters",
    Base.metadata,
    Column("scene_id", ForeignKey("scenes.id"), primary_key=True),
    Column("character_id", ForeignKey("characters.id"), primary_key=True),
)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    genre: Mapped[str] = mapped_column(String(80), default="slice of life")
    studio: Mapped[str] = mapped_column(String(120), default="")
    director_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    production_manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    start_date: Mapped[date | None] = mapped_column(Date)
    target_completion_date: Mapped[date | None] = mapped_column(Date)
    episode_count: Mapped[int] = mapped_column(Integer, default=12)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.PLANNING, index=True
    )

    director: Mapped["User | None"] = relationship(foreign_keys=[director_id])
    production_manager: Mapped["User | None"] = relationship(foreign_keys=[production_manager_id])
    episodes: Mapped[list[Episode]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    characters: Mapped[list[Character]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")
    milestones: Mapped[list["ProductionMilestone"]] = relationship(back_populates="project")


class Episode(Base, TimestampMixin):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    target_release_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[EpisodeStatus] = mapped_column(
        Enum(EpisodeStatus), default=EpisodeStatus.PLANNING, index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    director_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    production_manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    project: Mapped[Project] = relationship(back_populates="episodes")
    director: Mapped["User | None"] = relationship(foreign_keys=[director_id])
    production_manager: Mapped["User | None"] = relationship(foreign_keys=[production_manager_id])
    scenes: Mapped[list[Scene]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="episode")
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(back_populates="episode")


class Character(Base, TimestampMixin):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    role: Mapped[str] = mapped_column(String(80), default="supporting")

    project: Mapped[Project] = relationship(back_populates="characters")
    scenes: Mapped[list[Scene]] = relationship(secondary=scene_characters, back_populates="characters")


class Scene(Base, TimestampMixin):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"), index=True, nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(200), default="")
    props: Mapped[str] = mapped_column(Text, default="[]")
    duration_seconds: Mapped[int] = mapped_column(Integer, default=8)
    complexity: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.MEDIUM)
    assigned_artist_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[SceneStatus] = mapped_column(Enum(SceneStatus), default=SceneStatus.BACKLOG)
    production_stage: Mapped[ProductionStage] = mapped_column(
        Enum(ProductionStage), default=ProductionStage.SCRIPT, index=True
    )
    revision_count: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[float] = mapped_column(Float, default=0.0)

    episode: Mapped[Episode] = relationship(back_populates="scenes")
    assigned_artist: Mapped["User | None"] = relationship(foreign_keys=[assigned_artist_id])
    characters: Mapped[list[Character]] = relationship(
        secondary=scene_characters, back_populates="scenes"
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="scene")
    file_versions: Mapped[list["FileVersion"]] = relationship(back_populates="scene")
    reviews: Mapped[list["Review"]] = relationship(back_populates="scene")
    revision_requests: Mapped[list["RevisionRequest"]] = relationship(back_populates="scene")
    comments: Mapped[list["Comment"]] = relationship(back_populates="scene")

    @property
    def display_id(self) -> str:
        return f"SCN-{self.scene_number:03d}"

    @property
    def kanban_column(self) -> KanbanColumn:
        return STAGE_TO_KANBAN[self.production_stage]
