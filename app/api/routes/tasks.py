from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.tasks import (
    TaskCreate,
    TaskCreateResponse,
    TaskDeleteResponse,
    TaskPriority,
    TaskRead,
    TaskStatus,
)
from app.services.task_service import (
    create_task,
    delete_task,
    get_task_with_id,
    get_tasks,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/", response_model=TaskCreateResponse, status_code=status.HTTP_201_CREATED
)
def add(
    task_in: TaskCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    new_task = create_task(task_in, db, current_user.id)
    return {"message": "Task created successfully", "task": new_task}


@router.get("/", response_model=list[TaskRead])
def get(
    db: DbSession,
    current_user: CurrentUser,
    status_: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: TaskPriority | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return get_tasks(db, current_user.id, status_, priority, skip, limit)


@router.get("/{task_id}", response_model=TaskRead)
def get_with_id(db: DbSession, current_user: CurrentUser, task_id: int):
    return get_task_with_id(task_id, db, current_user.id)


@router.delete(
    "/delete/{task_id}",
    response_model=TaskDeleteResponse,
)
def delete(task_id: int, db: DbSession, current_user: CurrentUser):
    deleted = delete_task(task_id, db, current_user.id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {"message": f"Task with id - {task_id} deleted successfully"}
