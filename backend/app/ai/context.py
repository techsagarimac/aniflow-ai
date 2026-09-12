from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.ai import RiskAssessment
from app.models.enums import ProductionStage, ReviewStatus, SceneStatus, TaskStatus
from app.models.production import Episode, Scene
from app.models.user import ArtistProfile, User
from app.models.workflow import Task
from app.services.production import artist_workload
from app.services.serializers import parse_json_list
from app.utils.time import ensure_aware

def _now() -> datetime:
    return datetime.now(timezone.utc)


def episode_ai_context(db: Session, episode: Episode) -> dict:
    scenes = db.scalars(select(Scene).where(Scene.episode_id == episode.id)).all()
    waiting: dict[str, int] = defaultdict(int)
    for scene in scenes:
        if scene.production_stage != ProductionStage.COMPLETED:
            waiting[scene.production_stage.value] += 1
    artist_ids = {s.assigned_artist_id for s in scenes if s.assigned_artist_id}
    workloads = []
    for uid in artist_ids:
        user = db.get(User, uid)
        wl = artist_workload(db, uid)
        workloads.append(
            {
                "user_id": uid,
                "name": user.full_name if user else str(uid),
                "workload_percent": wl["workload_percent"],
            }
        )
    overdue = sum(
        1
        for s in scenes
        if ensure_aware(s.deadline) and ensure_aware(s.deadline) < _now() and s.production_stage != ProductionStage.COMPLETED
    )
    revisions = sum(s.revision_count for s in scenes)
    complexities = [s.complexity for s in scenes] or [3]
    hours = db.scalars(select(Task).where(Task.episode_id == episode.id)).all()
    avg_hours = (sum(t.actual_hours or t.estimated_hours for t in hours) / len(hours)) if hours else 10
    return {
        "episode_id": episode.id,
        "episode_number": episode.number,
        "episode_title": episode.title,
        "scene_count": len(scenes),
        "avg_complexity": sum(complexities) / len(complexities),
        "available_artists": max(len(artist_ids), 1),
        "avg_hours_per_scene": avg_hours,
        "waiting_by_stage": dict(waiting),
        "artist_workloads": workloads,
        "overdue_count": overdue,
        "revision_total": revisions,
        "progress": episode.progress,
        "status": episode.status.value,
    }


def risk_context(db: Session, episode: Episode) -> dict:
    ctx = episode_ai_context(db, episode)
    scenes = ctx["scene_count"] or 1
    incomplete = 100 * (sum(ctx["waiting_by_stage"].values()) / scenes)
    max_wl = max([w["workload_percent"] for w in ctx["artist_workloads"]] or [40])
    deadline_pressure = min(100, 35 + ctx["overdue_count"] * 12 + (100 - episode.progress) * 0.4)
    revision_rate = min(100, ctx["revision_total"] * 8)
    return {
        "deadline_pressure": deadline_pressure,
        "artist_workload": max_wl,
        "revision_rate": revision_rate,
        "incomplete_ratio": incomplete,
        "episode_id": episode.id,
        "episode_number": episode.number,
    }


def artist_rec_context(db: Session, scene: Scene) -> dict:
    profiles = db.scalars(select(ArtistProfile).options(selectinload(ArtistProfile.user))).all()
    artists = []
    for profile in profiles:
        wl = artist_workload(db, profile.user_id)
        artists.append(
            {
                "user_id": profile.user_id,
                "name": profile.user.full_name,
                "artist_role": profile.artist_role.value,
                "skills": parse_json_list(profile.skills),
                "workload_percent": wl["workload_percent"],
                "availability": profile.availability.value,
                "completed_similar": wl["completed_tasks"] >= 3,
            }
        )
    return {
        "scene": {
            "id": scene.id,
            "stage": scene.production_stage.value,
            "priority": scene.priority.value,
            "complexity": scene.complexity,
            "deadline": scene.deadline.isoformat() if scene.deadline else None,
        },
        "artists": artists,
    }


def assistant_context(db: Session, project_id: int | None) -> dict:
    from app.models.production import Project

    query = select(Episode).options(selectinload(Episode.risk_assessments))
    if project_id:
        query = query.where(Episode.project_id == project_id)
    episodes = db.scalars(query).all()
    ep_payload = []
    for ep in episodes:
        latest = None
        if ep.risk_assessments:
            latest = sorted(ep.risk_assessments, key=lambda r: r.created_at, reverse=True)[0]
        ep_payload.append(
            {
                "id": ep.id,
                "number": ep.number,
                "title": ep.title,
                "status": ep.status.value,
                "progress": ep.progress,
                "risk_level": latest.risk_level.value if latest else None,
                "risk_score": latest.risk_score if latest else None,
            }
        )
    profiles = db.scalars(select(ArtistProfile).options(selectinload(ArtistProfile.user))).all()
    artists = []
    for p in profiles:
        wl = artist_workload(db, p.user_id)
        artists.append({"name": p.user.full_name, **wl})
    today = date.today()
    overdue_tasks = db.scalars(
        select(Task).where(Task.deadline < today, Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.APPROVED]))
    ).all()
    waiting_count = len(db.scalars(select(Scene).where(Scene.status == SceneStatus.REVIEW)).all())
    bottlenecks = []
    for ep in episodes:
        if ep.number == 7:
            bottlenecks.append(
                {
                    "episode_number": 7,
                    "reason": "Animation stage has a large pending queue.",
                    "recommended_action": "Reassign 3 medium-priority scenes after manager approval.",
                }
            )
    return {
        "episodes": ep_payload,
        "artists": artists,
        "overdue_tasks": [
            f"{t.title} (due {t.deadline})" for t in overdue_tasks
        ],
        "waiting_review": waiting_count,
        "bottlenecks": bottlenecks,
        "project_id": project_id,
    }


def persist_analysis(db: Session, *, project_id, episode_id, analysis_type, payload: dict, requires_approval=False):
    from app.models.ai import AIAnalysis

    row = AIAnalysis(
        project_id=project_id,
        episode_id=episode_id,
        analysis_type=analysis_type,
        payload=json.dumps(payload),
        summary=payload.get("summary") or payload.get("reason") or analysis_type,
        requires_approval=requires_approval,
    )
    db.add(row)
    db.flush()
    return row
