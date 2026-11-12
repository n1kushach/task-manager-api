from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.tasks import TaskCreate


def create_task(task_in: TaskCreate, db: Session, owner_id: int) -> Task:
    task = Task(**task_in.model_dump(), owner_id=owner_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
