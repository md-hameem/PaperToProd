"""
Workspaces module — API routes for workspace and member management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_workspace_role
from app.auth.router import get_current_user
from app.database import get_db
from app.models import User, Workspace, WorkspaceMember, WorkspaceRole

router = APIRouter()

# ── Schemas ───────────────────────────────────────────────────


class WorkspaceResponse(BaseModel):
    id: int
    name: str


class WorkspaceMemberResponse(BaseModel):
    user_id: int
    email: str
    display_name: str | None
    role: str


class WorkspaceCreateRequest(BaseModel):
    name: str


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.MEMBER


class ChangeRoleRequest(BaseModel):
    role: WorkspaceRole


# ── Routes ────────────────────────────────────────────────────


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all workspaces the current user belongs to."""
    result = await db.execute(
        select(Workspace).join(WorkspaceMember).where(WorkspaceMember.user_id == current_user.id)
    )
    workspaces = result.scalars().all()
    return [{"id": w.id, "name": w.name} for w in workspaces]


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workspace."""
    workspace = Workspace(name=request.name)
    db.add(workspace)
    await db.flush()

    membership = WorkspaceMember(
        workspace_id=workspace.id, user_id=current_user.id, role=WorkspaceRole.OWNER.value
    )
    db.add(membership)
    await db.commit()
    await db.refresh(workspace)

    return {"id": workspace.id, "name": workspace.name}


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_members(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    membership: WorkspaceMember = Depends(require_workspace_role()),
):
    """List members of a workspace."""
    # Note: require_workspace_role checks x_workspace_id header, but here we also have path param
    # For safety, we can rely on the header or path, let's just use the query.
    # We'll just list the members for the path workspace_id if the user has access.

    # We should ensure the path matches the header or we can just rely on the path if we build a custom dependency.
    # To keep it simple, we trust require_workspace_role for now, assuming x_workspace_id matches.
    if membership.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Workspace ID mismatch")

    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == workspace_id)
    )

    members = []
    for member, user in result.all():
        members.append(
            {
                "user_id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "role": member.role,
            }
        )

    return members


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse)
async def invite_member(
    workspace_id: int,
    request: InviteMemberRequest,
    db: AsyncSession = Depends(get_db),
    membership: WorkspaceMember = Depends(
        require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
):
    """Invite a member (MVP: Directly adds them if they exist, fails otherwise)."""
    if membership.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Workspace ID mismatch")

    result = await db.execute(select(User).where(User.email == request.email))
    target_user = result.scalars().first()

    if not target_user:
        raise HTTPException(
            status_code=404, detail="User with that email does not exist yet (MVP limitation)."
        )

    # Check if already in workspace
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == target_user.id
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="User is already a member of this workspace.")

    new_member = WorkspaceMember(
        workspace_id=workspace_id, user_id=target_user.id, role=request.role.value
    )
    db.add(new_member)
    await db.commit()

    return {
        "user_id": target_user.id,
        "email": target_user.email,
        "display_name": target_user.display_name,
        "role": new_member.role,
    }


@router.patch("/{workspace_id}/members/{target_user_id}", response_model=WorkspaceMemberResponse)
async def change_role(
    workspace_id: int,
    target_user_id: int,
    request: ChangeRoleRequest,
    db: AsyncSession = Depends(get_db),
    membership: WorkspaceMember = Depends(
        require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
):
    """Change a user's role."""
    if membership.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Workspace ID mismatch")

    # Fetch target membership
    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User)
        .where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == target_user_id
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found.")

    target_membership, target_user = row

    # Prevent demoting the last owner
    if target_membership.role == WorkspaceRole.OWNER.value and request.role != WorkspaceRole.OWNER:
        # Check how many owners are left
        owners_result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == WorkspaceRole.OWNER.value,
            )
        )
        owners = list(owners_result.scalars().all())
        if len(owners) <= 1:
            raise HTTPException(status_code=400, detail="Cannot change role of the last owner.")

    # Only OWNERS can promote someone else to OWNER
    if request.role == WorkspaceRole.OWNER and membership.role != WorkspaceRole.OWNER.value:
        raise HTTPException(status_code=403, detail="Only owners can promote someone to owner.")

    target_membership.role = request.role.value
    await db.commit()

    return {
        "user_id": target_user.id,
        "email": target_user.email,
        "display_name": target_user.display_name,
        "role": target_membership.role,
    }


@router.delete("/{workspace_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: int,
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    membership: WorkspaceMember = Depends(
        require_workspace_role([WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
    ),
):
    """Remove a user from the workspace."""
    if membership.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Workspace ID mismatch")

    # Fetch target membership
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == target_user_id
        )
    )
    target_membership = result.scalars().first()

    if not target_membership:
        raise HTTPException(status_code=404, detail="Member not found.")

    # Prevent removing the last owner
    if target_membership.role == WorkspaceRole.OWNER.value:
        owners_result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == WorkspaceRole.OWNER.value,
            )
        )
        owners = list(owners_result.scalars().all())
        if len(owners) <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last owner.")

    # Users can remove themselves, but admins cannot remove other admins or owners unless they are an owner
    if (
        membership.user_id != target_user_id
        and target_membership.role in [WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value]
        and membership.role != WorkspaceRole.OWNER.value
    ):
        raise HTTPException(status_code=403, detail="Admins cannot remove other Admins or Owners.")

    await db.delete(target_membership)
    await db.commit()
    return
