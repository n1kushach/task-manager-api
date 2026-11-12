from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.tasks import TaskCreate, TaskPriority, TaskStatus, TaskUpdate


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
) -> list[Task]:
    query = select(Task).where(Task.owner_id == owner_id)

    if status is not None:
        query.where(Task.status == status.value)
    if priority is not None:
        query.where(Task.priority == priority)

    query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


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
    db: Session, task_id: int, owner_id: int, task_in: TaskUpdate
) -> Task | None:
    task = db.scalars(
        select(Task).where(Task.id == task_id, Task.owner_id == owner_id)
    ).first()
    if task is None:
        return None

    updates = task_in.model_dump(exclude_unset=True)

    # guard: these columns can't be NULL, so ignore explicit nulls
    for field in ("title", "status", "priority"):
        if updates.get(field, ...) is None:
            updates.pop(field)

    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task
