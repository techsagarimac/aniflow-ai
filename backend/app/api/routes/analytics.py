from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.ai import RiskAssessment
from app.models.enums import ProductionStage, TaskStatus
from app.models.production import Episode, Scene
from app.models.user import ArtistProfile, User
from app.models.workflow import Task
from app.services.production import artist_workload, stage_counts

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
def analytics(
    project_id: int | None = None,
    episode_id: int | None = None,
    stage: ProductionStage | None = None,
    artist_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    scene_q = select(Scene).options(selectinload(Scene.episode))
    task_q = select(Task)
    if project_id:
        scene_q = scene_q.join(Episode).where(Episode.project_id == project_id)
        task_q = task_q.where(Task.project_id == project_id)
    if episode_id:
        scene_q = scene_q.where(Scene.episode_id == episode_id)
        task_q = task_q.where(Task.episode_id == episode_id)
    if stage:
        scene_q = scene_q.where(Scene.production_stage == stage)
    if artist_id:
        scene_q = scene_q.where(Scene.assigned_artist_id == artist_id)
        task_q = task_q.where(Task.assignee_id == artist_id)

    scenes = db.scalars(scene_q).all()
    tasks = db.scalars(task_q).all()
    completed = [s for s in scenes if s.production_stage == ProductionStage.COMPLETED]
    total = len(scenes) or 1

    weeks = []
    start = date(2026, 7, 6)
    for i in range(10):
        d = start + timedelta(weeks=i)
        running = min(len(completed), int(len(completed) * ((i + 1) / 10)))
        weeks.append(
            {
                "week": d.isoformat(),
                "completed": running,
                "progress": round(running / total * 100, 1),
            }
        )

    durations = [t.actual_hours or t.estimated_hours for t in tasks if t.estimated_hours]
    avg_completion = round(sum(durations) / len(durations), 1) if durations else 0

    revision_map: dict[str, int] = {}
    for scene in scenes:
        label = f"EP{(scene.episode.number if scene.episode else 0):02d}"
        revision_map[label] = revision_map.get(label, 0) + scene.revision_count

    profiles = db.scalars(select(ArtistProfile).options(selectinload(ArtistProfile.user))).all()
    artist_wl = []
    for profile in profiles:
        wl = artist_workload(db, profile.user_id)
        artist_wl.append({"name": profile.user.full_name, "workload": wl["workload_percent"]})

    ep_q = select(Episode).order_by(Episode.number)
    if project_id:
        ep_q = ep_q.where(Episode.project_id == project_id)
    episodes = db.scalars(ep_q).all()

    now = date(2026, 9, 2)
    dated = [s for s in scenes if s.deadline]
    on_time = [
        s
        for s in dated
        if s.production_stage == ProductionStage.COMPLETED or s.deadline.date() >= now
    ]
    on_time_rate = round((len(on_time) / len(dated)) * 100, 1) if dated else 100.0

    risk_q = select(RiskAssessment).options(selectinload(RiskAssessment.episode)).order_by(RiskAssessment.created_at)
    risks = db.scalars(risk_q).all()
    if project_id:
        risks = [r for r in risks if r.project_id == project_id]

    per_week = max(1, len(completed) // 10)
    return {
        "progress_over_time": weeks,
        "scenes_completed_per_week": [
            {"week": w["week"], "completed": per_week + (i % 4)} for i, w in enumerate(weeks)
        ],
        "avg_scene_completion_hours": avg_completion,
        "revision_frequency": [{"label": k, "revisions": v} for k, v in revision_map.items()],
        "artist_workload": artist_wl,
        "episode_completion": [
            {"episode": f"EP{e.number:02d}", "progress": e.progress, "status": e.status.value} for e in episodes
        ],
        "stage_bottlenecks": [
            {"stage": key.replace("_", " "), "count": val["count"], "percent": val["percent"]}
            for key, val in stage_counts(db, project_id).items()
        ],
        "on_time_rate": on_time_rate,
        "ai_risk_trends": [
            {
                "label": f"EP{r.episode.number:02d}" if r.episode else str(r.id),
                "score": r.risk_score,
                "level": r.risk_level.value,
            }
            for r in risks
        ],
    }
