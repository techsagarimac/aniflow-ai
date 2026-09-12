from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import NotificationType, UserRole
from app.models.production import Scene
from app.models.user import User
from app.models.workflow import Task
from app.schemas import TaskCreate, TaskOut, TaskUpdate
from app.services.notifications import notify
from app.services.serializers import task_out

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _query():
    return select(Task).options(
        selectinload(Task.assignee),
        selectinload(Task.scene),
        selectinload(Task.episode),
    )


@router.get("", response_model=list[TaskOut])
def list_tasks(
    project_id: int | None = None,
    episode_id: int | None = None,
    assignee_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = _query()
    if project_id:
        query = query.where(Task.project_id == project_id)
    if episode_id:
        query = query.where(Task.episode_id == episode_id)
    if user.role == UserRole.ARTIST:
        query = query.where(Task.assignee_id == user.id)
    elif assignee_id:
        query = query.where(Task.assignee_id == assignee_id)
    tasks = db.scalars(query.order_by(Task.deadline)).all()
    return [task_out(t) for t in tasks]


@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR)),
):
    task = Task(**payload.model_dump())
    db.add(task)
    if task.assignee_id:
        notify(
            db,
            user_id=task.assignee_id,
            ntype=NotificationType.TASK_ASSIGNED,
            title=f"Task assigned: {task.title}",
            message="A new production task was assigned to you.",
            entity_type="task",
            entity_id=task.id,
        )
    db.commit()
    task = db.scalar(_query().where(Task.id == task.id))
    return task_out(task)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.scalar(_query().where(Task.id == task_id))
    if not task:
        raise HTTPException(404, "Task not found")
    if user.role == UserRole.ARTIST and task.assignee_id != user.id:
        raise HTTPException(403, "Artists can only view assigned tasks")
    return task_out(task)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if user.role == UserRole.ARTIST:
        if task.assignee_id != user.id:
            raise HTTPException(403, "Cannot update this task")
        data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if k in {"status", "actual_hours"}}
    elif user.role in {UserRole.ADMIN, UserRole.PRODUCTION_MANAGER, UserRole.DIRECTOR}:
        data = payload.model_dump(exclude_unset=True)
    else:
        raise HTTPException(403, "Cannot update tasks")
    prev_assignee = task.assignee_id
    for key, value in data.items():
        setattr(task, key, value)
    if task.assignee_id and task.assignee_id != prev_assignee:
        notify(
            db,
            user_id=task.assignee_id,
            ntype=NotificationType.TASK_ASSIGNED,
            title=f"Task assigned: {task.title}",
            message="You were assigned a production task.",
            entity_type="task",
            entity_id=task.id,
        )
    db.commit()
    task = db.scalar(_query().where(Task.id == task_id))
    return task_out(task)
