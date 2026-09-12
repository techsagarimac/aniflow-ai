from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import Priority, TaskStatus, TaskType


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), index=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("episodes.id"), index=True)
    scene_id: Mapped[int | None] = mapped_column(ForeignKey("scenes.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[TaskType] = mapped_column(Enum(TaskType), default=TaskType.GENERAL)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.MEDIUM)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO, index=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    deadline: Mapped[date | None] = mapped_column(Date)
    estimated_hours: Mapped[float] = mapped_column(Float, default=8.0)
    actual_hours: Mapped[float] = mapped_column(Float, default=0.0)

    project: Mapped["Project | None"] = relationship(back_populates="tasks")
    episode: Mapped["Episode | None"] = relationship(back_populates="tasks")
    scene: Mapped["Scene | None"] = relationship(back_populates="tasks")
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])


class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), nullable=False)
    artist_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"))
    assigned_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(40), default="active")
    notes: Mapped[str] = mapped_column(Text, default="")
    ai_recommended: Mapped[bool] = mapped_column(default=False)
    manager_approved: Mapped[bool] = mapped_column(default=True)

    scene: Mapped["Scene"] = relationship()
    artist: Mapped["User"] = relationship(foreign_keys=[artist_id])
    assigned_by: Mapped["User | None"] = relationship(foreign_keys=[assigned_by_id])


class ProductionMilestone(Base, TimestampMixin):
    __tablename__ = "production_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True, nullable=False)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("episodes.id"))
    scene_id: Mapped[int | None] = mapped_column(ForeignKey("scenes.id"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    type: Mapped[str] = mapped_column(String(40), default="milestone")
    status: Mapped[str] = mapped_column(String(40), default="upcoming")

    project: Mapped["Project"] = relationship(back_populates="milestones")
