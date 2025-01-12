from typing import AsyncGenerator
from contextlib import asynccontextmanager

from app import settings
from app.clients.dynamo_client import DynamoDBClient
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository


@asynccontextmanager
async def task_repository_factory() -> AsyncGenerator[TaskRepository, None]:
    async with DynamoDBClient.create_client(
        table_name=settings.TABLE_ARNS["tasks"]
    ) as operational_client:
        yield TaskRepository(dynamo_client=operational_client)


@asynccontextmanager
async def user_repository_factory() -> AsyncGenerator[UserRepository, None]:
    async with DynamoDBClient.create_client(
        table_name=settings.TABLE_ARNS["users"]
    ) as operational_client:
        yield UserRepository(dynamo_client=operational_client)


async def get_user_repository() -> UserRepository:
    async with user_repository_factory() as repo:
        return repo
