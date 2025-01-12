from typing import AsyncIterator, Optional
from aiodynamo.expressions import UpdateExpression

from app.schemas.task import Task
from app.clients.dynamo_client import DynamoDBClient


class TaskRepository:
    def __init__(self, dynamo_client: DynamoDBClient):
        self.client = dynamo_client

    async def create_task(self, task: Task) -> Task:
        await self.client.put_item(task.model_dump())
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        item = await self.client.get_item({"task_id": task_id})
        return Task.model_validate(item)

    async def update_task(
        self, task_id: str, update_expression: UpdateExpression
    ) -> Optional[Task]:
        await self.client.update_item({"task_id": task_id}, update_expression)
        task = await self.client.get_item({"task_id": task_id})
        return Task.model_validate(task)

    async def delete_task(self, task_id: str) -> None:
        await self.client.delete_item({"task_id": task_id})

    async def list_tasks(self, user) -> AsyncIterator[dict]:
        async for item in self.client.query():
            yield Task.model_validate(item)

    async def get_task_by_owner(self, owner_email: str) -> AsyncIterator[dict]:
        async for item in self.client.query(
            key_conditions=self.client.get_key_condition_equals(
                "owner_email", owner_email
            ),
            index_name="tasks_owner_email",
        ):
            yield Task.model_validate(item)
