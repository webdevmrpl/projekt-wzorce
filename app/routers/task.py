from fastapi import HTTPException, Depends, Query, Request
from fastapi import APIRouter
from typing import Optional
from datetime import datetime
from app.settings import security, security_scheme

from app.schemas.task import TaskCreateRequest, TaskStatuses, TaskUpdateRequest, Task
from app.schemas.user import User
from app.services.task_service import TaskService
from app.services.utils import get_task_service
from app.strategies.task_filter_strategy import get_filter_strategy
from app.strategies.task_sort_strategy import get_sort_strategy

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=Task, dependencies=[Depends(security_scheme)])
async def create_task(
    dto: TaskCreateRequest,
    current_user: User = Depends(security.get_current_subject),
    service: TaskService = Depends(get_task_service),
):
    task = await service.create_task(dto, current_user)
    return task


@router.get("/{task_id}", response_model=Task, dependencies=[Depends(security_scheme)])
async def get_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(security.get_current_subject),
):
    task = await service.get_task(task_id)
    if not task or task.owner_email != current_user.email:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=Task, dependencies=[Depends(security_scheme)])
async def update_task(
    task_id: str,
    dto: TaskUpdateRequest,
    current_user: User = Depends(security.get_current_subject),
    service: TaskService = Depends(get_task_service),
):
    task = await service.update_task(task_id, dto, current_user)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", dependencies=[Depends(security_scheme)])
async def delete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(security.get_current_subject),
):
    await service.delete_task(task_id)
    return {"detail": "Task deleted"}


@router.get("", response_model=list[Task], dependencies=[Depends(security_scheme)])
async def list_tasks(
    status: Optional[TaskStatuses] = Query(None, description="Filter tasks by status"),
    due_before: Optional[datetime] = Query(
        None, description="Filter tasks due before this date"
    ),
    sort_by: Optional[str] = Query(
        None, description="Sort by 'created_at' or 'priority'"
    ),
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(security.get_current_subject),
):
    filter_strategy = get_filter_strategy(status, due_before)
    sort_strategy = get_sort_strategy(sort_by)

    tasks = await service.list_tasks(
        filter_strategy=filter_strategy, sort_strategy=sort_strategy, user=current_user
    )
    return tasks


@router.post("/{task_id}/complete", response_model=Task)
async def mark_task_completed(
    task_id: str, service: TaskService = Depends(get_task_service)
):
    task = await service.mark_task_completed(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
