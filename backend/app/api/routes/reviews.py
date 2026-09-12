from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import NotificationType, ProductionStage, ReviewStatus, RevisionStatus, SceneStatus, UserRole
from app.models.files import Comment, Review, RevisionRequest
from app.models.production import Scene
from app.models.user import User
from app.schemas import CommentCreate, CommentOut, ReviewCreate, ReviewOut, RevisionCreate, RevisionOut, RevisionUpdate
from app.services.notifications import notify
from app.services.production import recompute_episode_progress, stage_progress
from app.services.serializers import comment_out, review_out, revision_out

router = APIRouter(tags=["reviews"])


@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(
    scene_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Review).options(selectinload(Review.reviewer))
    if scene_id:
        query = query.where(Review.scene_id == scene_id)
    return [review_out(r) for r in db.scalars(query.order_by(Review.created_at.desc())).all()]


@router.post("/reviews", response_model=ReviewOut, status_code=201)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.REVIEWER, UserRole.DIRECTOR, UserRole.PRODUCTION_MANAGER)),
):
    scene = db.get(Scene, payload.scene_id)
    if not scene:
        raise HTTPException(404, "Scene not found")
    review = Review(
        scene_id=payload.scene_id,
        file_version_id=payload.file_version_id,
        reviewer_id=user.id,
        status=payload.status,
        comments=payload.comments,
    )
    db.add(review)
    if payload.status == ReviewStatus.APPROVED:
        scene.status = SceneStatus.APPROVED
        notify(
            db,
            user_id=scene.assigned_artist_id or user.id,
            ntype=NotificationType.SCENE_APPROVED,
            title=f"{scene.display_id} approved",
            message=payload.comments or "Scene version approved.",
            entity_type="scene",
            entity_id=scene.id,
        )
    elif payload.status == ReviewStatus.REVISION_REQUIRED:
        scene.status = SceneStatus.REVISION
        scene.revision_count += 1
    db.commit()
    review = db.scalar(select(Review).options(selectinload(Review.reviewer)).where(Review.id == review.id))
    return review_out(review)


@router.get("/revisions", response_model=list[RevisionOut])
def list_revisions(
    scene_id: int | None = None,
    assigned_to_me: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(RevisionRequest).options(
        selectinload(RevisionRequest.assigned_to),
        selectinload(RevisionRequest.created_by),
    )
    if scene_id:
        query = query.where(RevisionRequest.scene_id == scene_id)
    if assigned_to_me or user.role == UserRole.ARTIST:
        query = query.where(RevisionRequest.assigned_to_id == user.id)
    return [revision_out(r) for r in db.scalars(query.order_by(RevisionRequest.created_at.desc())).all()]


@router.post("/revisions", response_model=RevisionOut, status_code=201)
def create_revision(
    payload: RevisionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.REVIEWER, UserRole.DIRECTOR, UserRole.PRODUCTION_MANAGER)),
):
    scene = db.get(Scene, payload.scene_id)
    if not scene:
        raise HTTPException(404, "Scene not found")
    rev = RevisionRequest(
        scene_id=payload.scene_id,
        review_id=payload.review_id,
        issue=payload.issue,
        priority=payload.priority,
        comment=payload.comment,
        assigned_to_id=payload.assigned_to_id or scene.assigned_artist_id,
        created_by_id=user.id,
        status=RevisionStatus.OPEN,
    )
    db.add(rev)
    scene.status = SceneStatus.REVISION
    scene.revision_count += 1
    if rev.assigned_to_id:
        notify(
            db,
            user_id=rev.assigned_to_id,
            ntype=NotificationType.REVISION_REQUESTED,
            title=f"Revision requested for {scene.display_id}",
            message=payload.issue,
            entity_type="scene",
            entity_id=scene.id,
        )
    db.commit()
    rev = db.scalar(
        select(RevisionRequest)
        .options(selectinload(RevisionRequest.assigned_to), selectinload(RevisionRequest.created_by))
        .where(RevisionRequest.id == rev.id)
    )
    return revision_out(rev)


@router.patch("/revisions/{revision_id}", response_model=RevisionOut)
def update_revision(
    revision_id: int,
    payload: RevisionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rev = db.get(RevisionRequest, revision_id)
    if not rev:
        raise HTTPException(404, "Revision not found")
    if user.role == UserRole.ARTIST and rev.assigned_to_id != user.id:
        raise HTTPException(403, "Cannot update this revision")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rev, key, value)
    db.commit()
    rev = db.scalar(
        select(RevisionRequest)
        .options(selectinload(RevisionRequest.assigned_to), selectinload(RevisionRequest.created_by))
        .where(RevisionRequest.id == revision_id)
    )
    return revision_out(rev)


@router.post("/scenes/{scene_id}/advance")
def advance_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.REVIEWER, UserRole.DIRECTOR, UserRole.PRODUCTION_MANAGER)),
):
    from app.models.enums import PRODUCTION_STAGES
    from app.models.production import Episode
    from app.api.routes.scenes import _get
    from app.services.serializers import scene_out

    scene = db.get(Scene, scene_id)
    if not scene:
        raise HTTPException(404, "Scene not found")
    stages = list(PRODUCTION_STAGES)
    idx = stages.index(scene.production_stage)
    if idx < len(stages) - 1:
        scene.production_stage = stages[idx + 1]
        scene.progress = stage_progress(scene.production_stage)
        scene.status = (
            SceneStatus.COMPLETED if scene.production_stage == ProductionStage.COMPLETED else SceneStatus.IN_PROGRESS
        )
    episode = db.get(Episode, scene.episode_id)
    if episode:
        recompute_episode_progress(db, episode)
    db.commit()
    return scene_out(_get(db, scene.id))


@router.get("/scenes/{scene_id}/comments", response_model=list[CommentOut])
def list_comments(scene_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Comment).options(selectinload(Comment.user)).where(Comment.scene_id == scene_id).order_by(Comment.created_at)
    ).all()
    return [comment_out(c) for c in rows]


@router.post("/scenes/{scene_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    scene_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.get(Scene, scene_id):
        raise HTTPException(404, "Scene not found")
    row = Comment(scene_id=scene_id, user_id=user.id, body=payload.body)
    db.add(row)
    db.commit()
    row = db.scalar(select(Comment).options(selectinload(Comment.user)).where(Comment.id == row.id))
    return comment_out(row)
