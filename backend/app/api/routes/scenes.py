from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import KANBAN_TO_STAGE, KanbanColumn, UserRole
from app.models.production import Character, Episode, Scene
from app.models.user import User
from app.schemas import SceneCreate, SceneOut, SceneUpdate
from app.services.production import recompute_episode_progress, stage_progress
from app.services.serializers import scene_out

router = APIRouter(prefix="/scenes", tags=["scenes"])


def _scene_query():
    return select(Scene).options(
        selectinload(Scene.assigned_artist),
        selectinload(Scene.characters),
        selectinload(Scene.episode),
    )


def _get(db: Session, scene_id: int) -> Scene:
    scene = db.scalar(_scene_query().where(Scene.id == scene_id))
    if not scene:
        raise HTTPException(404, "Scene not found")
    return scene


def _can_mutate_scene(user: User, scene: Scene) -> bool:
    if user.role in {UserRole.ADMIN, UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR}:
        return True
    if user.role == UserRole.ARTIST and scene.assigned_artist_id == user.id:
        return True
    return False


@router.get("", response_model=list[SceneOut])
def list_scenes(
    project_id: int | None = None,
    episode_id: int | None = None,
    assigned_to_me: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = _scene_query()
    if episode_id:
        query = query.where(Scene.episode_id == episode_id)
    if project_id:
        query = query.join(Episode).where(Episode.project_id == project_id)
    if assigned_to_me or user.role == UserRole.ARTIST:
        query = query.where(Scene.assigned_artist_id == user.id)
    scenes = db.scalars(query.order_by(Scene.scene_number)).all()
    return [scene_out(s) for s in scenes]


@router.post("", response_model=SceneOut, status_code=201)
def create_scene(
    payload: SceneCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR)),
):
    data = payload.model_dump()
    character_ids = data.pop("character_ids", [])
    props = data.pop("props", [])
    scene = Scene(**data, props=json.dumps(props), progress=stage_progress(payload.production_stage))
    if character_ids:
        scene.characters = list(db.scalars(select(Character).where(Character.id.in_(character_ids))).all())
    db.add(scene)
    db.commit()
    scene = _get(db, scene.id)
    recompute_episode_progress(db, scene.episode)
    db.commit()
    return scene_out(scene)


@router.get("/{scene_id}", response_model=SceneOut)
def get_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scene = _get(db, scene_id)
    if user.role == UserRole.ARTIST and scene.assigned_artist_id != user.id:
        raise HTTPException(403, "Artists can only view assigned scenes")
    return scene_out(scene)


@router.patch("/{scene_id}", response_model=SceneOut)
def update_scene(
    scene_id: int,
    payload: SceneUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scene = _get(db, scene_id)
    if not _can_mutate_scene(user, scene):
        raise HTTPException(403, "You cannot update this scene")
    data = payload.model_dump(exclude_unset=True)
    if user.role == UserRole.ARTIST:
        allowed = {"progress", "status"}
        data = {k: v for k, v in data.items() if k in allowed}

    if "kanban_column" in data:
        column = data.pop("kanban_column")
        if isinstance(column, str):
            column = KanbanColumn(column)
        data["production_stage"] = KANBAN_TO_STAGE[column]
    if "props" in data:
        scene.props = json.dumps(data.pop("props"))
    if "character_ids" in data:
        ids = data.pop("character_ids") or []
        scene.characters = list(db.scalars(select(Character).where(Character.id.in_(ids))).all()) if ids else []
    for key, value in data.items():
        setattr(scene, key, value)
    if "production_stage" in data:
        scene.progress = stage_progress(scene.production_stage)
    db.commit()
    scene = _get(db, scene.id)
    recompute_episode_progress(db, scene.episode)
    db.commit()
    return scene_out(scene)
