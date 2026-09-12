from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.ai import RiskAssessment
from app.models.production import Episode, Project, Scene
from app.models.user import ArtistProfile, User
from app.models.workflow import ProductionMilestone, Task
from app.services.production import artist_workload, dashboard_metrics, stage_counts
from app.services.serializers import milestone_out, parse_json_list, parse_json_obj, scene_out
from app.utils.time import ensure_aware

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(
    project_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if project_id is None:
        project = db.scalar(select(Project).order_by(Project.id))
        if not project:
            raise HTTPException(404, "No projects")
        project_id = project.id
    metrics = dashboard_metrics(db, project_id)
    stages = stage_counts(db, project_id)
    profiles = db.scalars(select(ArtistProfile).options(selectinload(ArtistProfile.user))).all()
    workload = []
    for p in profiles:
        wl = artist_workload(db, p.user_id)
        workload.append(
            {
                "user_id": p.user_id,
                "name": p.user.full_name,
                "role": p.artist_role.value,
                "avatar_color": p.user.avatar_color,
                **wl,
            }
        )
    workload.sort(key=lambda x: x["workload_percent"], reverse=True)

    risks = db.scalars(
        select(RiskAssessment)
        .options(selectinload(RiskAssessment.episode))
        .where(RiskAssessment.project_id == project_id)
        .order_by(RiskAssessment.created_at.desc())
    ).all()
    seen = set()
    bottlenecks = []
    for risk in risks:
        if risk.episode_id in seen:
            continue
        seen.add(risk.episode_id)
        if risk.risk_level.value in {"high", "critical", "medium"}:
            recs = parse_json_list(risk.recommendations)
            bottlenecks.append(
                {
                    "episode_id": risk.episode_id,
                    "episode_number": risk.episode.number if risk.episode else None,
                    "episode_title": risk.episode.title if risk.episode else None,
                    "risk_level": risk.risk_level.value,
                    "risk_score": risk.risk_score,
                    "reason": recs[0] if recs else "Production pressure detected.",
                    "predicted_delay": risk.predicted_delay_days,
                    "recommendations": recs,
                    "factors": parse_json_obj(risk.factors),
                    "requires_manager_approval": True,
                }
            )

    now = datetime.now(timezone.utc)
    milestones = db.scalars(
        select(ProductionMilestone)
        .where(ProductionMilestone.project_id == project_id)
        .order_by(ProductionMilestone.due_date)
    ).all()
    upcoming = [milestone_out(m) for m in milestones if ensure_aware(m.due_date) and ensure_aware(m.due_date) >= now][:8]
    episodes = db.scalars(
        select(Episode)
        .options(selectinload(Episode.director), selectinload(Episode.production_manager))
        .where(Episode.project_id == project_id)
        .order_by(Episode.number)
    ).all()
    return {
        "project_id": project_id,
        "metrics": metrics,
        "stage_progress": stages,
        "artist_workload": workload,
        "bottlenecks": bottlenecks[:4],
        "upcoming_deadlines": upcoming,
        "episodes": [
            {
                "id": e.id,
                "number": e.number,
                "title": e.title,
                "status": e.status.value,
                "progress": e.progress,
            }
            for e in episodes
        ],
    }


@router.get("/calendar")
def calendar(
    project_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if project_id is None:
        project = db.scalar(select(Project).order_by(Project.id))
        project_id = project.id if project else None
    events = []
    if project_id:
        scenes = db.scalars(
            select(Scene)
            .options(selectinload(Scene.episode), selectinload(Scene.assigned_artist), selectinload(Scene.characters))
            .join(Episode)
            .where(Episode.project_id == project_id, Scene.deadline.is_not(None))
        ).all()
        for s in scenes:
            events.append(
                {
                    "id": f"scene-{s.id}",
                    "title": f"{s.display_id} deadline",
                    "date": s.deadline.isoformat(),
                    "type": "scene_deadline",
                    "status": s.production_stage.value,
                    "entity_type": "scene",
                    "entity_id": s.id,
                    "priority": s.priority.value,
                }
            )
        episodes = db.scalars(select(Episode).where(Episode.project_id == project_id)).all()
        for e in episodes:
            if e.target_release_date:
                events.append(
                    {
                        "id": f"ep-{e.id}",
                        "title": f"Episode {e.number:02d} lock",
                        "date": e.target_release_date.isoformat(),
                        "type": "episode_deadline",
                        "status": e.status.value,
                        "entity_type": "episode",
                        "entity_id": e.id,
                    }
                )
        milestones = db.scalars(
            select(ProductionMilestone).where(ProductionMilestone.project_id == project_id)
        ).all()
        for m in milestones:
            events.append(
                {
                    "id": f"ms-{m.id}",
                    "title": m.title,
                    "date": m.due_date.isoformat(),
                    "type": m.type,
                    "status": m.status,
                    "entity_type": "milestone",
                    "entity_id": m.id,
                    "scene_id": m.scene_id,
                    "episode_id": m.episode_id,
                }
            )
    return {"events": events}


@router.get("/search")
def search(
    q: str = "",
    project_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    term = (q or "").strip().lower()
    if len(term) < 2:
        return {"scenes": [], "episodes": [], "tasks": []}
    scene_q = select(Scene).options(selectinload(Scene.episode), selectinload(Scene.assigned_artist), selectinload(Scene.characters))
    ep_q = select(Episode)
    task_q = select(Task).options(selectinload(Task.assignee), selectinload(Task.scene), selectinload(Task.episode))
    if project_id:
        scene_q = scene_q.join(Episode).where(Episode.project_id == project_id)
        ep_q = ep_q.where(Episode.project_id == project_id)
        task_q = task_q.where(Task.project_id == project_id)
    if user.role.value == "artist":
        scene_q = scene_q.where(Scene.assigned_artist_id == user.id)
        task_q = task_q.where(Task.assignee_id == user.id)
    scenes = [
        scene_out(s)
        for s in db.scalars(scene_q).all()
        if term in s.description.lower() or term in s.display_id.lower() or term in s.location.lower()
    ][:8]
    episodes = [
        {"id": e.id, "number": e.number, "title": e.title, "status": e.status.value}
        for e in db.scalars(ep_q).all()
        if term in e.title.lower() or term in f"{e.number:02d}"
    ][:8]
    from app.services.serializers import task_out

    tasks = [task_out(t) for t in db.scalars(task_q).all() if term in t.title.lower()][:8]
    return {"scenes": scenes, "episodes": episodes, "tasks": tasks}
