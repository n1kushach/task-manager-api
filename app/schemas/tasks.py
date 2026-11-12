from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.check_not_past import check_not_past


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None


class TaskCreate(TaskBase):
    """Payload for creating a task. owner_id comes from the authenticated user, not the client."""

    _check_due_date = field_validator("due_date")(check_not_past)


class TaskUpdate(BaseModel):
    """All fields optional for PATCH-style partial updates."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None

    _check_due_date = field_validator("due_date")(check_not_past)


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class TaskCreateResponse(BaseModel):
    message: str
    task: TaskRead
