from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.tasks import (
    PaginatedTaskResponse,
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)


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
) -> PaginatedTaskResponse:
    filters = [Task.owner_id == owner_id]
    if status is not None:
        filters.append(Task.status == status.value)
    if priority is not None:
        filters.append(Task.priority == priority.value)

    total = db.scalar(select(func.count()).select_from(Task).where(*filters)) or 0

    tasks = db.scalars(
        select(Task)
        .where(*filters)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return PaginatedTaskResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        skip=skip,
        limit=limit,
        has_more=skip + len(tasks) < total,
    )


def get_task_with_id(task_id: int, db: Session, owner_id: int) -> Task | None:
    query = select(Task).where(Task.owner_id == owner_id, Task.id == task_id)
    return db.scalars(query).first()


def delete_task(task_id: int, db: Session, owner_id: int) -> bool:
    task = db.scalars(
        select(Task).where(Task.id == task_id, Task.owner_id == owner_id)
    ).first()
    if task is None:
        return False
    db.delete(task)
    db.commit()
    return True


def update_task(
    db: Session,
    task_id: int,
    owner_id: int,
    task_in: TaskUpdate,
) -> Task | None:
    task = db.scalars(
        select(Task).where(
            Task.id == task_id,
            Task.owner_id == owner_id,
        )
    ).first()

    if task is None:
        return None

    update_data = task_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field in ("title", "status", "priority") and value is None:
            raise ValueError(f"{field} cannot be null!")

        setattr(task, field, value)

    try:
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise

    return task
