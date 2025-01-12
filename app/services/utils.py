import os
from typing import AsyncGenerator

from app.settings import security
from app.services.user_service import UserService
from app.services.task_service import TaskService
from app.repositories.factories import task_repository_factory, user_repository_factory
from app.observers.task_observers import (
    OverdueNotifier,
    ChangeHistoryObserver,
    SlackNotifier,
    PriorityEscalationNotifier,
)


async def get_user_service() -> AsyncGenerator[UserService, None]:
    async with user_repository_factory() as repo:
        yield UserService(repository=repo, security=security)


async def get_task_service() -> AsyncGenerator[TaskService, None]:
    async with task_repository_factory() as repo:
        slack_notifier = SlackNotifier(
            webhook_url=os.getenv("SLACK_WEBHOOK_URL", "http://localhost:8080")
        )
        observers = [
            OverdueNotifier(slack_notifier=slack_notifier),
            ChangeHistoryObserver(),
            slack_notifier,
            PriorityEscalationNotifier(slack_notifier=slack_notifier),
        ]

        yield TaskService(repository=repo, observers=observers)
