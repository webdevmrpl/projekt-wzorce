import asyncio
from concurrent.futures import ThreadPoolExecutor
from authx import TokenPayload
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.repositories.factories import user_repository_factory
from app.services.utils import get_user_service
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserLogin, UserUpdate, User, UserPermission
from app.settings import security
from app.permissions.permissions import check_user_has_access

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_create: UserCreate, user_service: UserService = Depends(get_user_service)
):
    """
    Endpoint for user registration.
    """
    try:
        return await user_service.create_user(user_create)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=dict, status_code=status.HTTP_200_OK)
async def login_user(
    response: Response,
    user_login_request: UserLogin,
    user_service: UserService = Depends(get_user_service),
):
    """
    Endpoint for user login.
    """
    try:
        access_token, refresh_token = await user_service.authenticate_user(
            email=user_login_request.email, password=user_login_request.password
        )
        security.set_access_cookies(token=access_token, response=response)
        security.set_refresh_cookies(token=refresh_token, response=response)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def get_current_user(
    current_user: User = Depends(security.get_current_subject),
):
    """
    Retrieve the current authenticated user's profile.
    """
    return current_user


@router.put(
    "/{email}",
    response_model=User,
    dependencies=[Depends(security.access_token_required)],
)
async def update_user(
    email: str,
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    """
    Update a user's information (admin access only).
    """
    try:
        return await user_service.update_user(email, user_update)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{email}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(check_user_has_access(permission=UserPermission.DELETE_USERS))
    ],
)
async def delete_user(
    email: str,
    user_service: UserService = Depends(get_user_service),
):
    """
    Delete a user by email (admin access only).
    """
    try:
        await user_service.delete_user(email)
        return {"detail": "User deleted"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/refresh")
async def get_new_access_token(
    response: Response,
    refresh: TokenPayload = Depends(security.refresh_token_required),
    user_service=Depends(get_user_service),
):
    user = await user_service.get_user(refresh.sub)
    access_token = security.create_access_token(
        uid=user.email, data={"roles": user.roles}
    )
    security.set_access_cookies(token=access_token, response=response)
    return {"access_token": access_token}


async def async_get_user_from_uuid(uuid: str):
    async with user_repository_factory() as user_repository:
        return await user_repository.get_user(email=uuid)


@security.set_subject_getter
def get_user_from_uuid(uuid: str):
    try:
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def run_async_in_new_loop(coro):
            return loop.run_until_complete(coro)

        future = executor.submit(run_async_in_new_loop, async_get_user_from_uuid(uuid))
        return future.result()

    finally:
        loop.close()
        executor.shutdown()
