from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_serializer, field_validator


class TaskStatuses(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskCreateRequest(BaseModel):
    title: str = Field(..., example="My Task")
    description: Optional[str] = Field(None, example="Task details...")
    status: TaskStatuses = Field("pending", example="pending")
    priority: int = Field(1, ge=1, le=5, example=3)
    due_date: datetime = Field(..., example="2025-12-31T23:59:59Z")

    @field_validator("due_date")
    def due_date_in_future(cls, v):
        if v <= datetime.now(timezone.utc):
            raise ValueError("due_date must be in the future.")
        return v


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, example="Updated Task Title")
    description: Optional[str] = Field(None, example="Updated description...")
    status: Optional[TaskStatuses] = Field(None, example="completed")
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[datetime] = Field(None, example="2025-12-31T23:59:59Z")

    @field_validator("due_date")
    def due_date_in_future(cls, v):
        if v and v <= datetime.now(timezone.utc):
            raise ValueError("due_date must be in the future.")
        return v


class Task(BaseModel):
    owner_email: str = Field(..., example="owner_email")
    task_id: str = Field(..., example="task_title_owner_email")
    title: str = Field(..., example="My Task")
    description: Optional[str] = Field(None, example="Task details...")
    status: TaskStatuses = Field("pending", example="pending")
    priority: int = Field(1, ge=1, le=5, example=3)
    notifier_id: Optional[str] = Field(None, example="celery_notifier_id")
    due_date: datetime = Field(..., example="2021-12-31T23:59:59Z")
    created_at: datetime = Field(..., example="2021-01-01T00:00:00Z")
    updated_at: datetime = Field(..., example="2021-01-01T00:00:00Z")

    @field_serializer("due_date", "created_at", "updated_at")
    def datetime_to_str(self, value):
        return value.strftime("%Y-%m-%d %H:%M:%S.%f") if value else None


class TaskServiceActions(str, Enum):
    task_created = "task_created"
    task_updated = "task_updated"
    task_deleted = "task_deleted"
    mark_task_completed = "mark_task_completed"


def convert_datetime(value):
    return value.strftime("%Y-%m-%d %H:%M:%S.%f")


async def async_iterator_to_list(async_iterator):
    return [item async for item in async_iterator]
