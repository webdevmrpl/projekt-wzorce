from app.settings import security, ROLE_PERMISSIONS
from app.schemas.user import User, UserPermission
from fastapi import Depends, HTTPException, status


def check_user_has_access(permission: UserPermission):
    async def dependency(user: User = Depends(security.get_current_subject)):
        if any([permission in ROLE_PERMISSIONS[role] for role in user.roles]):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this resource",
        )

    return dependency
