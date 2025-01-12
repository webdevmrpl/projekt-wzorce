from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from app.schemas.task import Task


class TaskSortStrategy(ABC):
    @abstractmethod
    def sort(self, tasks: List[Task]) -> List[Task]:
        pass


class SortByCreatedAtStrategy(TaskSortStrategy):
    def sort(self, tasks: List[Task]) -> List[Task]:
        return sorted(tasks, key=lambda t: t.created_at)


class SortByPriorityStrategy(TaskSortStrategy):
    def sort(self, tasks: List[Task]) -> List[Task]:
        return sorted(tasks, key=lambda t: t.priority)


class CompositeSortStrategy(TaskSortStrategy):
    def __init__(self, strategies: List[TaskSortStrategy]):
        self.strategies = strategies

    def sort(self, tasks: List[Task]) -> List[Task]:
        for strategy in reversed(self.strategies):
            tasks = strategy.sort(tasks)
        return tasks


def get_sort_strategy(
    sort_by: Optional[List[str]] = None,
) -> Optional[TaskSortStrategy]:

    if not sort_by:
        return None

    strategy_map = {
        "created_at": SortByCreatedAtStrategy(),
        "priority": SortByPriorityStrategy(),
    }

    strategies = [
        strategy_map[criteria] for criteria in sort_by if criteria in strategy_map
    ]

    if not strategies:
        return None
    elif len(strategies) == 1:
        return strategies[0]
    else:
        return CompositeSortStrategy(strategies)
