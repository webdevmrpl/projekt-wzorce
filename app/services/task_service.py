from hashlib import sha256
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, List
from aiodynamo.expressions import F

from app.observers.task_observers import TaskObserver
from app.repositories.task_repository import TaskRepository
from app.schemas.user import User
from app.schemas.task import async_iterator_to_list, convert_datetime
from app.strategies.task_sort_strategy import TaskSortStrategy
from app.strategies.task_filter_strategy import TaskFilterStrategy
from app.schemas.task import (
    Task,
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskServiceActions,
)


class TaskNotFoundError(Exception): ...


class InsufficientPermissionsError(Exception): ...


class TaskService:
    def __init__(
        self,
        repository: TaskRepository,
        observers: Optional[List[TaskObserver]] = None,
    ):
        self.repository = repository
        self.observers = observers or []

    def create_task_id(self, title: str, owner_email: str) -> str:
        return sha256(f"{title}_{owner_email}".encode()).hexdigest()

    async def create_task(self, request: TaskCreateRequest, user: User) -> Task:
        task = Task(
            **request.model_dump(),
            created_at=datetime.now(ZoneInfo("Europe/Warsaw")),
            updated_at=datetime.now(ZoneInfo("Europe/Warsaw")),
            owner_email=user.email,
            task_id=self.create_task_id(request.title, user.email),
        )
        await self.repository.create_task(task)
        await self._notify_observers(TaskServiceActions.task_created, task, None)
        return task

    async def update_task(
        self, task_id: str, dto: TaskUpdateRequest, user: User
    ) -> Optional[Task]:

        old_task = await self.repository.get_task(task_id)

        if not old_task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        if old_task.owner_email != user.email:
            raise InsufficientPermissionsError(
                f"User {user.email} does not have permission to update task {task_id}"
            )

        update_data = dto.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(ZoneInfo("Europe/Warsaw"))

        task = old_task.model_copy(deep=True)

        for key, value in update_data.items():
            setattr(task, key, value)

        await self.repository.create_task(task)

        await self._notify_observers(TaskServiceActions.task_updated, task, old_task)

        return task

    async def get_task(self, task_id: str) -> Optional[dict]:
        return await self.repository.get_task(task_id)

    async def delete_task(self, task_id: str) -> None:
        await self.repository.delete_task(task_id)

    async def list_tasks(
        self,
        user: User,
        filter_strategy: Optional[TaskFilterStrategy] = None,
        sort_strategy: Optional[TaskSortStrategy] = None,
    ) -> List[dict]:
        tasks = await async_iterator_to_list(
            self.repository.get_task_by_owner(user.email)
        )
        if filter_strategy:
            tasks = filter_strategy.filter(tasks)
        if sort_strategy:
            tasks = sort_strategy.sort(tasks)
        return tasks

    async def mark_task_completed(self, task_id: str) -> Optional[dict]:
        old_task = await self.repository.get_task(task_id)
        if not old_task:
            return None
        task = await self.repository.update_task(
            task_id,
            F("status").set("completed")
            & F("updated_at").set(
                convert_datetime(datetime.now(ZoneInfo("Europe/Warsaw")))
            ),
        )
        if task:
            await self._notify_observers(
                TaskServiceActions.mark_task_completed, task, old_task
            )
        return task

    async def _notify_observers(
        self, action: TaskServiceActions, task: Task, old_task: Optional[Task]
    ) -> None:
        for obs in self.observers:
            await obs.update(action, task, old_task)
