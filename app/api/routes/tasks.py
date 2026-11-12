from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.tasks import TaskCreate, TaskCreateResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/", response_model=TaskCreateResponse, status_code=status.HTTP_201_CREATED
)
def create_task(
    task_in: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    task = Task(**task_in.model_dump(), owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"message": "Task created successfully", "task": task}


# @router.get("/", response_model=TaskRead)
# def get_tasks(current_user: Annotated[User, Depends]):
#     pass
