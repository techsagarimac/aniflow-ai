from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import UserRole
from app.models.production import Character, Project
from app.models.user import User
from app.schemas import CharacterOut, ProjectCreate, ProjectOut, ProjectUpdate
from app.services.production import project_progress
from app.services.serializers import project_out

router = APIRouter(prefix="/projects", tags=["projects"])


def _load(db: Session, project_id: int) -> Project:
    project = db.scalar(
        select(Project)
        .options(selectinload(Project.director), selectinload(Project.production_manager))
        .where(Project.id == project_id)
    )
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    projects = db.scalars(
        select(Project).options(selectinload(Project.director), selectinload(Project.production_manager))
    ).all()
    out = []
    for p in projects:
        completed, overall = project_progress(db, p)
        out.append(project_out(p, completed, overall))
    return out


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR)),
):
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    project = _load(db, project.id)
    return project_out(project, 0, 0)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project = _load(db, project_id)
    completed, overall = project_progress(db, project)
    return project_out(project, completed, overall)


@router.get("/{project_id}/characters", response_model=list[CharacterOut])
def list_characters(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = db.scalars(select(Character).where(Character.project_id == project_id)).all()
    return [CharacterOut.model_validate(c) for c in rows]


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR)),
):
    project = _load(db, project_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    project = _load(db, project.id)
    completed, overall = project_progress(db, project)
    return project_out(project, completed, overall)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.PRODUCTION_MANAGER)),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    db.delete(project)
    db.commit()
