import uuid
import logging
from authx import AuthX
from typing import Optional, List
from passlib.context import CryptContext
from fastapi import HTTPException, status
from aiodynamo.expressions import UpdateExpression, F

from app.schemas.user import UserCreate, UserUpdate, User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, repository: UserRepository, security: AuthX):
        self.repository = repository
        self.security = security
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def generate_uid(self) -> str:
        return str(uuid.uuid4())

    async def create_user(self, user_create_request: UserCreate) -> User:
        user = User(
            **user_create_request.model_dump(exclude={"password"}),
            is_active=True,
            password=self.hash_password(user_create_request.password),
        )

        return await self.repository.create_user(user)

    async def authenticate_user(self, email: str, password: str) -> tuple[str, str]:
        user = await self.repository.get_user(email)
        if not user or not self.verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        access_token = self.security.create_access_token(
            uid=user.email, data={"roles": user.roles}
        )
        refresh_token = self.security.create_refresh_token(uid=user.email)
        return access_token, refresh_token

    async def get_user(self, email: str) -> Optional[User]:
        user = await self.repository.get_user(email)
        if not user:
            raise Exception(f"User with email {email} not found")
        return user

    async def update_user(self, email: str, user_update: UserUpdate) -> Optional[User]:
        updates = {
            k: v
            for k, v in user_update.model_dump(exclude_unset=True).items()
            if v is not None
        }
        update_expression = UpdateExpression()
        for key, value in updates.items():
            update_expression += F(key).set(value)

        updated_user = await self.repository.update_user(email, update_expression)
        if not updated_user:
            raise Exception(f"User with email {email} not found")
        return User.model_validate(updated_user)

    async def delete_user(self, email: str) -> None:
        user = await self.repository.get_user(email)
        if not user:
            raise Exception(f"User with email {email} not found")
        await self.repository.delete_user(email)
