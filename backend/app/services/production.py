from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import (
    EpisodeStatus,
    ProductionStage,
    RiskLevel,
    SceneStatus,
    TaskStatus,
)
from app.models.production import Episode, Project, Scene
from app.models.user import ArtistProfile, User
from app.models.workflow import Task
from app.services.serializers import ACTIVE_TASK_STATUSES
from app.utils.time import ensure_aware

STAGE_WEIGHT = {
    ProductionStage.SCRIPT: 5,
    ProductionStage.STORYBOARD: 15,
    ProductionStage.LAYOUT: 25,
    ProductionStage.KEY_ANIMATION: 40,
    ProductionStage.IN_BETWEEN: 55,
    ProductionStage.BACKGROUND: 65,
    ProductionStage.COLORING: 75,
    ProductionStage.COMPOSITING: 88,
    ProductionStage.QC: 95,
    ProductionStage.COMPLETED: 100,
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def stage_progress(stage: ProductionStage) -> float:
    return float(STAGE_WEIGHT.get(stage, 0))


def recompute_episode_progress(db: Session, episode: Episode) -> float:
    scenes = list(episode.scenes) if episode.scenes else db.scalars(
        select(Scene).where(Scene.episode_id == episode.id)
    ).all()
    if not scenes:
        episode.progress = 0
        return 0
    avg = sum(stage_progress(s.production_stage) for s in scenes) / len(scenes)
    episode.progress = round(avg, 1)
    if avg >= 100:
        episode.status = EpisodeStatus.COMPLETED
    return episode.progress


def project_progress(db: Session, project: Project) -> tuple[int, float]:
    episodes = db.scalars(select(Episode).where(Episode.project_id == project.id)).all()
    if not episodes:
        return 0, 0.0
    completed = sum(1 for e in episodes if e.status == EpisodeStatus.COMPLETED)
    overall = sum(e.progress for e in episodes) / len(episodes)
    return completed, round(overall, 1)


def artist_workload(db: Session, user_id: int) -> dict:
    tasks = db.scalars(select(Task).where(Task.assignee_id == user_id)).all()
    active = [t for t in tasks if t.status in ACTIVE_TASK_STATUSES]
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    hours = sum(t.estimated_hours for t in active)
    # 40h week capacity
    percent = round((hours / 40) * 100, 1) if hours else 0
    overdue = sum(1 for t in active if t.deadline and t.deadline < utcnow().date())
    if percent >= 100 or overdue >= 2:
        risk = "high"
    elif percent >= 75 or overdue:
        risk = "medium"
    else:
        risk = "low"
    return {
        "active_tasks": len(active),
        "completed_tasks": len(completed),
        "workload_percent": percent,
        "deadline_risk": risk,
        "overdue_tasks": overdue,
        "estimated_hours": hours,
    }


def stage_counts(db: Session, project_id: int | None = None) -> dict[str, dict]:
    query = select(Scene)
    if project_id:
        query = query.join(Episode).where(Episode.project_id == project_id)
    scenes = db.scalars(query).all()
    total = len(scenes) or 1
    counts: dict[str, int] = defaultdict(int)
    for scene in scenes:
        counts[scene.production_stage.value] += 1
    return {
        stage.value: {
            "count": counts[stage.value],
            "percent": round(counts[stage.value] / total * 100, 1),
        }
        for stage in ProductionStage
    }


def dashboard_metrics(db: Session, project_id: int) -> dict:
    project = db.get(Project, project_id)
    episodes = db.scalars(select(Episode).where(Episode.project_id == project_id)).all()
    scenes = db.scalars(
        select(Scene).join(Episode).where(Episode.project_id == project_id)
    ).all()
    now = utcnow()
    completed_eps = [e for e in episodes if e.status == EpisodeStatus.COMPLETED]
    in_prod_eps = [e for e in episodes if e.status not in {EpisodeStatus.COMPLETED, EpisodeStatus.PLANNING}]
    completed_scenes = [s for s in scenes if s.production_stage == ProductionStage.COMPLETED]
    in_prod_scenes = [
        s
        for s in scenes
        if s.production_stage not in {ProductionStage.SCRIPT, ProductionStage.COMPLETED}
    ]
    overdue = [s for s in scenes if ensure_aware(s.deadline) and ensure_aware(s.deadline) < now and s.production_stage != ProductionStage.COMPLETED]
    _, overall = project_progress(db, project) if project else (0, 0)
    return {
        "total_episodes": len(episodes),
        "completed_episodes": len(completed_eps),
        "episodes_in_production": len(in_prod_eps),
        "overall_progress": overall,
        "total_scenes": len(scenes),
        "completed_scenes": len(completed_scenes),
        "scenes_in_production": len(in_prod_scenes),
        "overdue_scenes": len(overdue),
    }
