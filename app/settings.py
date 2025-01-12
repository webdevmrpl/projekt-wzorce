import os
from datetime import timedelta
from authx import AuthX, AuthXConfig
from fastapi.security import HTTPBearer
from app.schemas.user import User, UserPermission

TABLE_ARNS = {
    "tasks": os.environ.get("TASKS_TABLE_NAME", "tasks"),
    "users": os.environ.get("USERS_TABLE_NAME", "users"),
}

auth_config = AuthXConfig(
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_TOKEN", "changeme"),
    JWT_TOKEN_LOCATION=["cookies", "headers"],
    JWT_ACCESS_COOKIE_NAME="my_access_token",
    JWT_REFRESH_COOKIE_NAME="my_refresh_token",
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=5),
)

security = AuthX(config=auth_config, model=User)
security_scheme = HTTPBearer()

ROLE_PERMISSIONS = {
    "admin": {*[role for role in UserPermission]},
    "user": {
        UserPermission.LIST_TASKS,
        UserPermission.CREATE_TASK,
        UserPermission.UPDATE_TASK,
        UserPermission.DELETE_TASK,
    },
}

OVERDUE_EMAIL_FROM_NAME = "Task Manager"
DEFAULT_REPLY_TO = "support@trial-neqvygmpzz8g0p7w.mlsender.net"
DEFAULT_EMAIL_FROM = "noreply@trial-neqvygmpzz8g0p7w.mlsender.net"
