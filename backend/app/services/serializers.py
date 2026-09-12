from __future__ import annotations

import json
from typing import Any

from app.models.enums import STAGE_TO_KANBAN, TaskStatus
from app.models.files import Comment, FileVersion, Review, RevisionRequest
from app.models.production import Episode, Project, Scene
from app.models.user import ArtistProfile, User
from app.models.workflow import ProductionMilestone, Task
from app.schemas import (
    ArtistProfileOut,
    CharacterOut,
    CommentOut,
    EpisodeOut,
    FileVersionOut,
    MilestoneOut,
    NotificationOut,
    ProjectOut,
    ReviewOut,
    RevisionOut,
    SceneOut,
    TaskOut,
    UserOut,
)


def parse_json_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def parse_json_obj(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def user_out(user: User | None) -> UserOut | None:
    return UserOut.model_validate(user) if user else None


def project_out(project: Project, completed_episodes: int = 0, overall_progress: float = 0) -> ProjectOut:
    data = ProjectOut.model_validate(project)
    return data.model_copy(
        update={
            "director": user_out(project.director),
            "production_manager": user_out(project.production_manager),
            "completed_episodes": completed_episodes,
            "overall_progress": overall_progress,
        }
    )


def episode_out(
    episode: Episode,
    *,
    scene_count: int = 0,
    revision_count: int = 0,
    risk_level=None,
    risk_score: float | None = None,
) -> EpisodeOut:
    data = EpisodeOut.model_validate(episode)
    return data.model_copy(
        update={
            "director": user_out(episode.director),
            "production_manager": user_out(episode.production_manager),
            "scene_count": scene_count,
            "revision_count": revision_count,
            "risk_level": risk_level,
            "risk_score": risk_score,
        }
    )


def scene_out(scene: Scene) -> SceneOut:
    data = SceneOut.model_validate(scene)
    return data.model_copy(
        update={
            "display_id": scene.display_id,
            "props": parse_json_list(scene.props),
            "kanban_column": STAGE_TO_KANBAN[scene.production_stage].value,
            "assigned_artist": user_out(scene.assigned_artist),
            "characters": [CharacterOut.model_validate(c) for c in scene.characters],
            "episode_number": scene.episode.number if scene.episode else None,
            "episode_title": scene.episode.title if scene.episode else None,
        }
    )


def task_out(task: Task) -> TaskOut:
    data = TaskOut.model_validate(task)
    return data.model_copy(
        update={
            "assignee": user_out(task.assignee),
            "scene_display_id": task.scene.display_id if task.scene else None,
            "episode_number": task.episode.number if task.episode else None,
        }
    )


def artist_out(
    profile: ArtistProfile,
    *,
    active_tasks: int = 0,
    completed_tasks: int = 0,
    workload_percent: float = 0,
    deadline_risk: str = "low",
) -> ArtistProfileOut:
    skills = parse_json_list(profile.skills)
    data = ArtistProfileOut.model_validate(profile)
    return data.model_copy(
        update={
            "skills": skills,
            "user": user_out(profile.user),
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "workload_percent": workload_percent,
            "deadline_risk": deadline_risk,
        }
    )


def review_out(review: Review) -> ReviewOut:
    data = ReviewOut.model_validate(review)
    return data.model_copy(update={"reviewer": user_out(review.reviewer)})


def revision_out(rev: RevisionRequest) -> RevisionOut:
    data = RevisionOut.model_validate(rev)
    return data.model_copy(
        update={
            "assigned_to": user_out(rev.assigned_to),
            "created_by": user_out(rev.created_by),
        }
    )


def comment_out(comment: Comment) -> CommentOut:
    data = CommentOut.model_validate(comment)
    return data.model_copy(update={"user": user_out(comment.user)})


def file_version_out(version: FileVersion) -> FileVersionOut:
    data = FileVersionOut.model_validate(version)
    return data.model_copy(
        update={
            "artist": user_out(version.artist),
            "download_url": f"/api/files/versions/{version.id}/download",
        }
    )


def milestone_out(m: ProductionMilestone) -> MilestoneOut:
    return MilestoneOut.model_validate(m)


def notification_out(n) -> NotificationOut:
    return NotificationOut.model_validate(n)


ACTIVE_TASK_STATUSES = {
    TaskStatus.TODO,
    TaskStatus.IN_PROGRESS,
    TaskStatus.REVIEW,
    TaskStatus.REVISION,
}
