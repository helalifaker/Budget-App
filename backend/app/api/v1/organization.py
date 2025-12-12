"""
Organization API Routes.

Endpoints for organization management.
For EFIR (single-tenant deployment), returns the default organization.

Mounted under /api/v1/organization.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import UserDep
from app.models.auth import Organization

router = APIRouter(prefix="/api/v1/organization", tags=["Organization"])


class OrganizationResponse(BaseModel):
    """Single organization details."""

    id: uuid.UUID
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class CurrentOrganizationResponse(BaseModel):
    """Response for current organization endpoint."""

    organization: OrganizationResponse | None
    is_default: bool


@router.get("/current", response_model=CurrentOrganizationResponse)
async def get_current_organization(
    db: AsyncSession = Depends(get_db),
    user: UserDep = ...,
) -> CurrentOrganizationResponse:
    """
    Get the current user's organization.

    For EFIR (single-tenant deployment), this returns the default organization.
    In a multi-tenant setup, this would return the organization associated
    with the authenticated user.

    Returns:
    - organization: The organization details (id, name, is_active)
    - is_default: Whether this is the default organization (true for single-tenant)
    """
    try:
        # For single-tenant: Get the first (and only) active organization
        # For multi-tenant: Would look up user's organization from their profile
        result = await db.execute(
            select(Organization)
            .where(Organization.is_active == True)  # noqa: E712
            .limit(1)
        )
        org = result.scalar_one_or_none()

        if org:
            return CurrentOrganizationResponse(
                organization=OrganizationResponse(
                    id=org.id,
                    name=org.name,
                    is_active=org.is_active,
                ),
                is_default=True,  # Single-tenant: always the default org
            )

        # No organization found - this shouldn't happen in a properly configured system
        return CurrentOrganizationResponse(
            organization=None,
            is_default=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve organization: {e!s}",
        ) from e


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserDep = ...,
) -> OrganizationResponse:
    """
    Get organization by ID.

    Returns the organization details for the specified ID.
    RLS policies ensure users can only access their own organization.
    """
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        is_active=org.is_active,
    )
