from datetime import date, datetime
from typing import Any
import json

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import (
    ArtistRole,
    Availability,
    EpisodeStatus,
    ExperienceLevel,
    FileKind,
    KanbanColumn,
    NotificationType,
    Priority,
    ProductionStage,
    ProjectStatus,
    ReviewStatus,
    RevisionStatus,
    RiskLevel,
    SceneStatus,
    TaskStatus,
    TaskType,
    UserRole,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserOut(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    avatar_color: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole
    avatar_color: str = "#7C9CFF"


class ArtistProfileOut(ORMModel):
    id: int
    user_id: int
    artist_role: ArtistRole
    skills: list[str] = []
    experience_level: ExperienceLevel
    availability: Availability
    avg_completion_hours: float
    user: UserOut | None = None
    active_tasks: int = 0
    completed_tasks: int = 0
    workload_percent: float = 0
    deadline_risk: str = "low"

    @field_validator("skills", mode="before")
    @classmethod
    def _skills(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return []


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    genre: str = "slice of life"
    studio: str = ""
    director_id: int | None = None
    production_manager_id: int | None = None
    start_date: date | None = None
    target_completion_date: date | None = None
    episode_count: int = 12
    status: ProjectStatus = ProjectStatus.PLANNING


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    genre: str | None = None
    studio: str | None = None
    director_id: int | None = None
    production_manager_id: int | None = None
    start_date: date | None = None
    target_completion_date: date | None = None
    episode_count: int | None = None
    status: ProjectStatus | None = None


class ProjectOut(ORMModel):
    id: int
    name: str
    description: str
    genre: str
    studio: str
    director_id: int | None
    production_manager_id: int | None
    start_date: date | None
    target_completion_date: date | None
    episode_count: int
    status: ProjectStatus
    director: UserOut | None = None
    production_manager: UserOut | None = None
    completed_episodes: int = 0
    overall_progress: float = 0


class EpisodeCreate(BaseModel):
    project_id: int
    number: int
    title: str
    description: str = ""
    target_release_date: date | None = None
    status: EpisodeStatus = EpisodeStatus.PLANNING
    director_id: int | None = None
    production_manager_id: int | None = None


class EpisodeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_release_date: date | None = None
    status: EpisodeStatus | None = None
    progress: float | None = None
    director_id: int | None = None
    production_manager_id: int | None = None


class EpisodeOut(ORMModel):
    id: int
    project_id: int
    number: int
    title: str
    description: str
    target_release_date: date | None
    status: EpisodeStatus
    progress: float
    director_id: int | None
    production_manager_id: int | None
    director: UserOut | None = None
    production_manager: UserOut | None = None
    scene_count: int = 0
    revision_count: int = 0
    risk_level: RiskLevel | None = None
    risk_score: float | None = None


class CharacterOut(ORMModel):
    id: int
    project_id: int
    name: str
    description: str
    role: str


class SceneCreate(BaseModel):
    episode_id: int
    scene_number: int
    description: str = ""
    location: str = ""
    props: list[str] = []
    character_ids: list[int] = []
    duration_seconds: int = 8
    complexity: int = 3
    priority: Priority = Priority.MEDIUM
    assigned_artist_id: int | None = None
    deadline: datetime | None = None
    status: SceneStatus = SceneStatus.BACKLOG
    production_stage: ProductionStage = ProductionStage.SCRIPT


class SceneUpdate(BaseModel):
    description: str | None = None
    location: str | None = None
    props: list[str] | None = None
    character_ids: list[int] | None = None
    duration_seconds: int | None = None
    complexity: int | None = None
    priority: Priority | None = None
    assigned_artist_id: int | None = None
    deadline: datetime | None = None
    status: SceneStatus | None = None
    production_stage: ProductionStage | None = None
    kanban_column: KanbanColumn | None = None
    progress: float | None = None


class SceneOut(ORMModel):
    id: int
    episode_id: int
    scene_number: int
    display_id: str
    description: str
    location: str
    props: list[str] = []
    duration_seconds: int
    complexity: int
    priority: Priority
    assigned_artist_id: int | None
    deadline: datetime | None
    status: SceneStatus
    production_stage: ProductionStage
    kanban_column: KanbanColumn
    revision_count: int
    progress: float
    assigned_artist: UserOut | None = None
    characters: list[CharacterOut] = []
    episode_number: int | None = None
    episode_title: str | None = None

    @field_validator("props", mode="before")
    @classmethod
    def _props(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return []


class TaskCreate(BaseModel):
    project_id: int | None = None
    episode_id: int | None = None
    scene_id: int | None = None
    title: str
    description: str = ""
    type: TaskType = TaskType.GENERAL
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    assignee_id: int | None = None
    start_date: date | None = None
    deadline: date | None = None
    estimated_hours: float = 8
    actual_hours: float = 0


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    type: TaskType | None = None
    priority: Priority | None = None
    status: TaskStatus | None = None
    assignee_id: int | None = None
    start_date: date | None = None
    deadline: date | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None


class TaskOut(ORMModel):
    id: int
    project_id: int | None
    episode_id: int | None
    scene_id: int | None
    title: str
    description: str
    type: TaskType
    priority: Priority
    status: TaskStatus
    assignee_id: int | None
    start_date: date | None
    deadline: date | None
    estimated_hours: float
    actual_hours: float
    assignee: UserOut | None = None
    scene_display_id: str | None = None
    episode_number: int | None = None


class ReviewCreate(BaseModel):
    scene_id: int
    file_version_id: int | None = None
    status: ReviewStatus
    comments: str = ""


class ReviewOut(ORMModel):
    id: int
    scene_id: int
    file_version_id: int | None
    reviewer_id: int
    status: ReviewStatus
    comments: str
    created_at: datetime
    reviewer: UserOut | None = None


class RevisionCreate(BaseModel):
    scene_id: int
    review_id: int | None = None
    issue: str
    priority: Priority = Priority.HIGH
    comment: str = ""
    assigned_to_id: int | None = None


class RevisionUpdate(BaseModel):
    status: RevisionStatus | None = None
    comment: str | None = None


class RevisionOut(ORMModel):
    id: int
    scene_id: int
    review_id: int | None
    issue: str
    priority: Priority
    comment: str
    assigned_to_id: int | None
    created_by_id: int | None
    status: RevisionStatus
    created_at: datetime
    assigned_to: UserOut | None = None
    created_by: UserOut | None = None


class CommentCreate(BaseModel):
    body: str


class CommentOut(ORMModel):
    id: int
    scene_id: int
    user_id: int
    body: str
    created_at: datetime
    user: UserOut | None = None


class FileVersionOut(ORMModel):
    id: int
    file_id: int
    scene_id: int | None
    version_number: int
    label: str
    mime_type: str
    size_bytes: int
    notes: str
    artist_id: int | None
    review_status: ReviewStatus
    created_at: datetime
    artist: UserOut | None = None
    download_url: str | None = None


class NotificationOut(ORMModel):
    id: int
    type: NotificationType
    title: str
    message: str
    is_read: bool
    related_entity_type: str | None
    related_entity_id: int | None
    created_at: datetime


class MilestoneOut(ORMModel):
    id: int
    project_id: int
    episode_id: int | None
    scene_id: int | None
    title: str
    due_date: datetime
    type: str
    status: str


class RiskOut(ORMModel):
    id: int
    project_id: int | None
    episode_id: int | None
    risk_score: float
    risk_level: RiskLevel
    factors: dict[str, Any]
    recommendations: list[Any]
    predicted_delay_days: str
    created_at: datetime


class ScheduleEstimateRequest(BaseModel):
    episode_id: int


class BottleneckRequest(BaseModel):
    project_id: int | None = None
    episode_id: int | None = None


class AssignmentRecRequest(BaseModel):
    scene_id: int


class ChatRequest(BaseModel):
    message: str
    project_id: int | None = None


class ApproveAnalysisRequest(BaseModel):
    approved: bool = True
