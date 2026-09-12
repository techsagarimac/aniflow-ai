from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.ai import RiskAssessment
from app.models.enums import UserRole
from app.models.production import Episode, Scene
from app.models.user import User
from app.schemas import EpisodeCreate, EpisodeOut, EpisodeUpdate
from app.services.production import recompute_episode_progress
from app.services.serializers import episode_out

router = APIRouter(prefix="/episodes", tags=["episodes"])


def _with_stats(db: Session, episode: Episode) -> EpisodeOut:
    scene_count = db.scalar(select(func.count(Scene.id)).where(Scene.episode_id == episode.id)) or 0
    revision_count = db.scalar(select(func.coalesce(func.sum(Scene.revision_count), 0)).where(Scene.episode_id == episode.id)) or 0
    risk = db.scalar(
        select(RiskAssessment)
        .where(RiskAssessment.episode_id == episode.id)
        .order_by(RiskAssessment.created_at.desc())
    )
    return episode_out(
        episode,
        scene_count=scene_count,
        revision_count=int(revision_count),
        risk_level=risk.risk_level if risk else None,
        risk_score=risk.risk_score if risk else None,
    )


@router.get("", response_model=list[EpisodeOut])
def list_episodes(
    project_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Episode).options(
        selectinload(Episode.director),
        selectinload(Episode.production_manager),
    )
    if project_id:
        query = query.where(Episode.project_id == project_id)
    episodes = db.scalars(query.order_by(Episode.number)).all()
    return [_with_stats(db, e) for e in episodes]


@router.post("", response_model=EpisodeOut, status_code=201)
def create_episode(
    payload: EpisodeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR)),
):
    episode = Episode(**payload.model_dump())
    db.add(episode)
    db.commit()
    db.refresh(episode)
    episode = db.scalar(
        select(Episode)
        .options(selectinload(Episode.director), selectinload(Episode.production_manager))
        .where(Episode.id == episode.id)
    )
    return _with_stats(db, episode)


@router.get("/{episode_id}", response_model=EpisodeOut)
def get_episode(
    episode_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    episode = db.scalar(
        select(Episode)
        .options(selectinload(Episode.director), selectinload(Episode.production_manager))
        .where(Episode.id == episode_id)
    )
    if not episode:
        raise HTTPException(404, "Episode not found")
    recompute_episode_progress(db, episode)
    db.commit()
    return _with_stats(db, episode)


@router.patch("/{episode_id}", response_model=EpisodeOut)
def update_episode(
    episode_id: int,
    payload: EpisodeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR)),
):
    episode = db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(404, "Episode not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(episode, key, value)
    db.commit()
    episode = db.scalar(
        select(Episode)
        .options(selectinload(Episode.director), selectinload(Episode.production_manager))
        .where(Episode.id == episode_id)
    )
    return _with_stats(db, episode)
