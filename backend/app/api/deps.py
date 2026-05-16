from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.user import User
from app.services.auth_service import get_user_from_token

security = HTTPBearer()


class PermissionChecker:
    def __init__(self, allowed_roles: list[str] | None = None):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        token = credentials.credentials
        user = await get_user_from_token(db, token, token_type="access")

        if self.allowed_roles and user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="auth.insufficient_permissions",
            )

        return user


# Common permission presets
get_current_user = PermissionChecker()
require_admin = PermissionChecker(["Admin"])
require_admin_or_manager = PermissionChecker(["Admin", "Manager"])
require_data_entry = PermissionChecker(["Admin", "Manager", "Agent"])
