from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.tasks import (
    TaskCreate,
    TaskCreateResponse,
    TaskPriority,
    TaskRead,
    TaskStatus,
)
from app.services.task_service import create_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/", response_model=TaskCreateResponse, status_code=status.HTTP_201_CREATED
)
def add(
    task_in: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    new_task = create_task(task_in, db, current_user.id)
    return {"message": "Task created successfully", "task": new_task}


@router.get("/", response_model=list[TaskRead])
def get_tasks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: TaskPriority | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    query = select(Task).where(Task.owner_id == current_user.id)

    if status_ is not None:
        query.where(Task.status == status_.value)
    if priority is not None:
        query.where(Task.priority == priority)
    query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
    return db.scalars(query).all()
