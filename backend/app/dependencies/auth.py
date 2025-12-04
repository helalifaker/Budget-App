"""
Authentication dependencies for FastAPI endpoints.

Provides user context from authenticated requests.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status


class CurrentUser:
    """
    Current authenticated user information.

    Extracted from JWT token by AuthenticationMiddleware.
    """

    def __init__(self, user_id: uuid.UUID, email: str, role: str, metadata: dict):
        """
        Initialize current user.

        Args:
            user_id: User UUID from Supabase Auth
            email: User email
            role: User role (admin, manager, planner, viewer)
            metadata: Additional user metadata
        """
        self.user_id = user_id
        self.email = email
        self.role = role
        self.metadata = metadata

    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == "admin"

    def is_manager(self) -> bool:
        """Check if user is a manager or admin."""
        return self.role in ["admin", "manager"]

    def is_planner(self) -> bool:
        """Check if user is a planner or higher."""
        return self.role in ["admin", "manager", "planner"]

    def can_write(self) -> bool:
        """Check if user can modify data."""
        return self.role in ["admin", "manager", "planner"]


async def get_current_user(request: Request) -> CurrentUser:
    """
    Get current authenticated user from request.

    Dependency that extracts user information from request state
    (set by AuthenticationMiddleware).

    Args:
        request: FastAPI request object

    Returns:
        CurrentUser instance with user information

    Raises:
        HTTPException: If user not authenticated

    Usage:
        ```python
        @router.get("/me")
        async def get_me(user: CurrentUser = Depends(get_current_user)):
            return {"user_id": user.user_id, "email": user.email}
        ```
    """
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Log the actual user_id value for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Attempting to convert user_id to UUID: {user_id} (type: {type(user_id)})")

    try:
        # Ensure user_id is a string before UUID conversion
        user_id_str = str(user_id).strip()
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, AttributeError, TypeError) as e:
        logger.error(
            f"Failed to convert user_id to UUID: {user_id} (type: {type(user_id)}), error: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user ID format: {user_id}",
        )

    return CurrentUser(
        user_id=user_uuid,
        email=getattr(request.state, "user_email", ""),
        role=getattr(request.state, "user_role", "viewer"),
        metadata=getattr(request.state, "user_metadata", {}),
    )


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Require admin role.

    Dependency that ensures the user is an admin.

    Args:
        user: Current authenticated user

    Returns:
        CurrentUser if admin

    Raises:
        HTTPException: If user is not an admin

    Usage:
        ```python
        @router.delete("/users/{id}")
        async def delete_user(
            id: UUID,
            user: CurrentUser = Depends(require_admin),
        ):
            # Only admins can reach this
            ...
        ```
    """
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_manager(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Require manager or admin role.

    Args:
        user: Current authenticated user

    Returns:
        CurrentUser if manager or admin

    Raises:
        HTTPException: If user is not manager or admin
    """
    if not user.is_manager():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required",
        )
    return user


async def require_planner(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Require planner, manager, or admin role.

    Args:
        user: Current authenticated user

    Returns:
        CurrentUser if planner, manager, or admin

    Raises:
        HTTPException: If user does not have write permissions
    """
    if not user.is_planner():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Planner, manager, or admin access required",
        )
    return user


# Type annotations for easier use
UserDep = Annotated[CurrentUser, Depends(get_current_user)]
AdminDep = Annotated[CurrentUser, Depends(require_admin)]
ManagerDep = Annotated[CurrentUser, Depends(require_manager)]
PlannerDep = Annotated[CurrentUser, Depends(require_planner)]
