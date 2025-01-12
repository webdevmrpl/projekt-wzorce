from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.schemas.task import Task


class TaskFilterStrategy(ABC):
    @abstractmethod
    def filter(self, tasks: List[Task]) -> List[Task]:
        pass


class StatusFilterStrategy(TaskFilterStrategy):
    def __init__(self, status: str):
        self.status = status

    def filter(self, tasks: List[Task]) -> List[Task]:
        return [task for task in tasks if task.status == self.status]


class DueDateFilterStrategy(TaskFilterStrategy):
    def __init__(self, due_before: datetime):
        self.due_before = due_before

    def filter(self, tasks: List[Task]) -> List[Task]:
        return [task for task in tasks if task.due_date <= self.due_before]


class CompositeFilterStrategy(TaskFilterStrategy):
    def __init__(self, strategies: List[TaskFilterStrategy]):
        self.strategies = strategies

    def filter(self, tasks: List[Task]) -> List[Task]:
        for strategy in self.strategies:
            tasks = strategy.filter(tasks)
        return tasks


def get_filter_strategy(
    status: Optional[str] = None, due_before: Optional[datetime] = None
) -> Optional[TaskFilterStrategy]:
    strategies: list[TaskFilterStrategy] = []
    if status:
        strategies.append(StatusFilterStrategy(status))
    if due_before:
        strategies.append(DueDateFilterStrategy(due_before))

    if len(strategies) == 1:
        return strategies[0]
    elif len(strategies) > 1:
        return CompositeFilterStrategy(strategies)
    else:
        return None
