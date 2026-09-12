from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin
from app.models.enums import FileKind, ReviewStatus, RevisionStatus, Priority


class FileAsset(Base, TimestampMixin):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    scene_id: Mapped[int | None] = mapped_column(ForeignKey("scenes.id"), index=True)
    kind: Mapped[FileKind] = mapped_column(Enum(FileKind), default=FileKind.OTHER)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    versions: Mapped[list[FileVersion]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )


class FileVersion(Base, TimestampMixin):
    __tablename__ = "file_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)
    scene_id: Mapped[int | None] = mapped_column(ForeignKey("scenes.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(40), default="v01")
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    artist_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus), default=ReviewStatus.PENDING
    )

    file: Mapped[FileAsset] = relationship(back_populates="versions")
    scene: Mapped["Scene | None"] = relationship(back_populates="file_versions")
    artist: Mapped["User | None"] = relationship(foreign_keys=[artist_id])
    reviews: Mapped[list["Review"]] = relationship(back_populates="file_version")


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True, nullable=False)
    file_version_id: Mapped[int | None] = mapped_column(ForeignKey("file_versions.id"))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    comments: Mapped[str] = mapped_column(Text, default="")

    scene: Mapped["Scene"] = relationship(back_populates="reviews")
    file_version: Mapped[FileVersion | None] = relationship(back_populates="reviews")
    reviewer: Mapped["User"] = relationship(foreign_keys=[reviewer_id])
    revision_requests: Mapped[list["RevisionRequest"]] = relationship(back_populates="review")


class RevisionRequest(Base, TimestampMixin):
    __tablename__ = "revision_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True, nullable=False)
    review_id: Mapped[int | None] = mapped_column(ForeignKey("reviews.id"))
    issue: Mapped[str] = mapped_column(String(300), nullable=False)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.HIGH)
    comment: Mapped[str] = mapped_column(Text, default="")
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[RevisionStatus] = mapped_column(
        Enum(RevisionStatus), default=RevisionStatus.OPEN, index=True
    )

    scene: Mapped["Scene"] = relationship(back_populates="revision_requests")
    review: Mapped[Review | None] = relationship(back_populates="revision_requests")
    assigned_to: Mapped["User | None"] = relationship(foreign_keys=[assigned_to_id])
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    scene: Mapped["Scene"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship()
