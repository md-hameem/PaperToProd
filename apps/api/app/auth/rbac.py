"""
Role-Based Access Control (RBAC) Module
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_db
from app.models import User, WorkspaceMember, WorkspaceRole


def require_workspace_role(allowed_roles: list[WorkspaceRole] | None = None):
    """
    Dependency factory that checks if the current user has the required role
    in the workspace specified by the X-Workspace-ID header.
    If allowed_roles is None, any role is sufficient (just needs to be a member).
    """

    async def role_checker(
        x_workspace_id: int = Header(..., description="The ID of the workspace"),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> WorkspaceMember:
        # Check membership
        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == x_workspace_id,
                WorkspaceMember.user_id == current_user.id,
            )
        )
        membership = result.scalars().first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this workspace.",
            )

        if allowed_roles and membership.role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role to perform this action in the workspace.",
            )

        return membership

    return role_checker
