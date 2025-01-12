import os
import logging

from yarl import URL
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Union

from aiodynamo.errors import ItemNotFound
from aiodynamo.client import Client, Table
from aiodynamo.http.aiohttp import AIOHTTP
from aiodynamo.credentials import Credentials
from aiodynamo.expressions import (
    Condition,
    F,
    HashKey,
    RangeKey,
    UpdateExpression,
    KeyCondition,
)

from aiohttp import ClientSession
from botocore.exceptions import BotoCoreError
from pydantic import BaseModel

from app import settings

logger = logging.getLogger(__name__)


class DynamoDBClientError(Exception): ...


class DynamoPageRequest(BaseModel):
    records: int = 100
    last_evaluated_key: Optional[dict]


class DynamoPage(BaseModel):
    items: list[dict]
    last_evaluated_key: Optional[dict]


def dynamo_error_handler(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BotoCoreError as e:
            logger.exception(f"Exception caught in {func.__name__}: {e}")
            raise DynamoDBClientError(f"DynamoDB error: {e}")

    return wrapper


class DynamoDBClient:
    def __init__(self, table: Table, client: Client):
        self.table: Table = table
        self.client: Client = client
        self.logger = logging.getLogger(__name__)

    def get_key_condition_equals(self, key: str, value: Union[str, int]) -> HashKey:
        return HashKey(key, value)

    def get_key_condition_begins_with(self, key: str, value: str) -> Condition:
        return RangeKey(key).begins_with(value)

    def get_filter_condition_equals(self, key: str, value: str) -> Condition:
        return F(key).equals(value)

    @property
    def table_name(self) -> str:
        return settings.TABLE_ARNS[self.table.name]

    def query(
        self,
        key_conditions: HashKey,
        filter_expression: Optional[Condition] = None,
        index_name: Optional[str] = None,
    ) -> AsyncIterator[dict]:
        if filter_expression:
            return self.table.query(
                key_condition=key_conditions,
                index=index_name,
                filter_expression=filter_expression,
            )
        return self.table.query(key_condition=key_conditions, index=index_name)

    async def query_single_page(
        self,
        key_conditions: HashKey,
        dynamo_page_request: DynamoPageRequest,
        filter_expression: Optional[Condition] = None,
        index_name: Optional[str] = None,
    ) -> DynamoPage:
        page = await self.table.query_single_page(
            key_condition=key_conditions,
            index=index_name,
            filter_expression=filter_expression,
            start_key=dynamo_page_request.last_evaluated_key,
            limit=dynamo_page_request.records,
        )
        return DynamoPage(items=page.items, last_evaluated_key=page.last_evaluated_key)

    @dynamo_error_handler
    async def get_item(self, key: dict[str, str]):
        try:
            return await self.table.get_item(key=key)
        except ItemNotFound:
            return None

    @dynamo_error_handler
    async def put_item(self, item: dict) -> Optional[dict]:
        return await self.table.put_item(item=item)

    @dynamo_error_handler
    async def update_item(
        self,
        key: dict[str, str],
        update_expression: UpdateExpression,
    ) -> Optional[dict]:
        return await self.table.update_item(
            key=key,
            update_expression=update_expression,
        )

    @dynamo_error_handler
    async def count_items(
        self, key_condition: KeyCondition, index_name: str, table: str
    ) -> int:
        return await self.client.count(
            table=table, key_condition=key_condition, index=index_name
        )

    @dynamo_error_handler
    async def get_all_items(self) -> AsyncIterator[dict]:
        async def async_gen():
            async for item in self.table.scan():
                yield item

        return async_gen()

    @asynccontextmanager
    @staticmethod
    async def create_client(table_name: str):
        async with ClientSession() as session:
            client = Client(
                AIOHTTP(session),
                Credentials.auto(),
                region=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                endpoint=(
                    URL(os.environ.get("DYNAMO_ENDPOINT_URL", ""))
                    if os.environ.get("DYNAMO_ENDPOINT_URL")
                    else None
                ),
            )
            table = client.table(table_name)
            yield DynamoDBClient(table=table, client=client)

    async def delete_item(self, key: dict[str, str]) -> None:
        await self.table.delete_item(key=key)

    async def scan(self) -> AsyncIterator[dict]:
        async for item in self.table.scan():
            yield item
