import logging
from typing import Optional
import requests

from zoneinfo import ZoneInfo
from celery import shared_task
from abc import ABC, abstractmethod
from aiodynamo.expressions import F
from celery.result import AsyncResult
from datetime import datetime, timedelta

from app.celery.celery import app as celery_app
from app.schemas.task import Task, TaskServiceActions
from app.repositories.factories import task_repository_factory
from app.observers.emailer import EmailRecipient, EmailBody, send_mail

logger = logging.getLogger(__name__)


def generate_email_info_model(task: dict) -> EmailBody:
    return EmailBody(
        recipients=[EmailRecipient(name="Test", email=task["owner_email"])],
        body=f"Task {task['title']} is overdue! Please take action!",
        subject=f"Task {task['title']} is overdue!",
    )


@shared_task(queue="tasks")
def create_due_date_notification(task_serialized: dict):
    email_info: EmailBody = generate_email_info_model(task_serialized)
    send_mail(email_info)
    return f'Email sent to {", ".join([r.email for r in email_info.recipients])}'


@shared_task(queue="tasks")
def send_slack_message(webhook_url: str, message: str):
    logger.info(f"[Slack] {message}. Sending message to Slack...")
    requests.post(webhook_url, json={"text": message})
    logger.info(f"[Slack] Message ({message}) sent!")


@shared_task(queue="tasks")
def celery_test_task(task: Task):
    logger.info(f"Task {task.task_id} is overdue! Please take action!")


class TaskObserver(ABC):
    @abstractmethod
    async def update(
        self, action: TaskServiceActions, task: Task, old_task: Optional[Task] = None
    ) -> None:
        """
        Called whenever a task is created or updated.
        `old_task` can be None if this is a newly created task.
        If `old_task` is provided, it can be used to detect changes.
        """
        pass


class SlackNotifier(TaskObserver):
    """
    Observer that triggers celery task to send a Slack message
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def update(
        self, action: TaskServiceActions, task: Task, old_task: Optional[Task] = None
    ) -> None:
        if action == TaskServiceActions.mark_task_completed:
            self._send_slack_message(f"Task {task.task_id} completed! Good job!")

    def _send_slack_message(self, message: str) -> None:
        send_slack_message.apply_async(args=[self.webhook_url, message])


class ChangeHistoryObserver(TaskObserver):
    """
    Stores a history of changes
    """

    async def update(
        self, action: TaskServiceActions, task: Task, old_task: Optional[Task] = None
    ) -> None:
        change_record = {
            "id": task.task_id,
            "old_task": old_task.model_dump() if old_task else None,
            "new_task": task.model_dump(),
            "timestamp": datetime.now(ZoneInfo("Europe/Warsaw")).isoformat(),
        }
        logger.debug(f"History updated for task {task.task_id}. Total history records")


class OverdueNotifier(TaskObserver):
    """
    Checks if a task is overdue and send email. Integrates with SlackNotifier for extra visibility.
    """

    def __init__(self, slack_notifier: SlackNotifier):
        self.slack_notifier = slack_notifier

    async def update(
        self, action: TaskServiceActions, task: Task, old_task: Optional[Task] = None
    ) -> None:
        async with task_repository_factory() as repo:
            if action == TaskServiceActions.task_created:
                res = create_due_date_notification.apply_async(
                    args=[task.model_dump()],
                    eta=task.due_date - timedelta(hours=1),
                )
                await repo.update_task(task.task_id, F("notifier_id").set(res.id))

            elif (
                action == TaskServiceActions.task_updated
                and task.due_date != old_task.due_date
            ):
                if old_task.notifier_id:
                    prev_res = AsyncResult(old_task.notifier_id, app=celery_app)
                    prev_res.revoke()
                res = create_due_date_notification.apply_async(
                    args=[task.model_dump()],
                    eta=task.due_date - timedelta(hours=1),
                )
                await repo.update_task(task.task_id, F("notifier_id").set(res.id))


class PriorityEscalationNotifier(TaskObserver):
    """
    If the task's priority is escalated to 5, log a special message and integrate with Slack.
    """

    def __init__(self, slack_notifier: SlackNotifier):
        self.slack_notifier = slack_notifier

    async def update(
        self, action: TaskServiceActions, task: Task, old_task: Optional[Task] = None
    ) -> None:
        old_priority = old_task.priority if old_task else 1
        new_priority = task.priority
        if new_priority == 5 and old_priority < 5:
            message = f"Task {task.title} priority escalated to 5! Immediate attention required!"
            logger.warning(message)
            self.slack_notifier._send_slack_message(message)
