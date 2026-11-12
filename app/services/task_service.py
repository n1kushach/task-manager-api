from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskPriority, TaskStatus


def create_task(task_in: TaskCreate, db: Session, owner_id: int) -> Task:
    task = Task(**task_in.model_dump(), owner_id=owner_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_tasks(
    db: Session,
    owner_id: int,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    skip: int = 0,
    limit: int = 20,
):
    query = select(Task).where(Task.owner_id == owner_id)

    if status is not None:
        query.where(Task.status == status.value)
    if priority is not None:
        query.where(Task.priority == priority)

    query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())
