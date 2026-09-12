from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.enums import ProductionStage
from app.models.production import Scene
from app.models.user import ArtistProfile, User
from app.models.workflow import Task
from app.schemas import ArtistProfileOut
from app.services.production import artist_workload
from app.services.serializers import artist_out

router = APIRouter(prefix="/artists", tags=["artists"])


@router.get("", response_model=list[ArtistProfileOut])
def list_artists(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    profiles = db.scalars(select(ArtistProfile).options(selectinload(ArtistProfile.user))).all()
    return [_decorate(db, p) for p in profiles]


@router.get("/{artist_id}", response_model=dict)
def get_artist(
    artist_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    profile = db.scalar(
        select(ArtistProfile)
        .options(selectinload(ArtistProfile.user))
        .where(ArtistProfile.user_id == artist_id)
    )
    if not profile:
        raise HTTPException(404, "Artist not found")
    scenes = db.scalars(
        select(Scene)
        .options(selectinload(Scene.episode), selectinload(Scene.assigned_artist), selectinload(Scene.characters))
        .where(Scene.assigned_artist_id == artist_id)
    ).all()
    tasks = db.scalars(select(Task).options(selectinload(Task.assignee), selectinload(Task.scene), selectinload(Task.episode)).where(Task.assignee_id == artist_id)).all()
    completed = [s for s in scenes if s.production_stage == ProductionStage.COMPLETED]
    revisions = sum(s.revision_count for s in scenes)
    from app.services.serializers import scene_out, task_out

    return {
        "profile": _decorate(db, profile),
        "active_scenes": [scene_out(s) for s in scenes if s.production_stage != ProductionStage.COMPLETED],
        "completed_scenes": [scene_out(s) for s in completed[:20]],
        "tasks": [task_out(t) for t in tasks],
        "revision_total": revisions,
        "avg_completion_hours": profile.avg_completion_hours,
    }


def _decorate(db: Session, profile: ArtistProfile) -> ArtistProfileOut:
    wl = artist_workload(db, profile.user_id)
    return artist_out(profile, **{k: wl[k] for k in ("active_tasks", "completed_tasks", "workload_percent", "deadline_risk")})
