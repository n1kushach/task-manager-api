from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.tasks import (
    TaskCreate,
    TaskCreateResponse,
    TaskPriority,
    TaskRead,
    TaskStatus,
)
from app.services.task_service import create_task, get_tasks

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
def get(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: TaskPriority | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return get_tasks(db, current_user.id, status_, priority, skip, limit)
