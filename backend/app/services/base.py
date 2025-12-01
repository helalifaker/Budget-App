"""
Base service class with common CRUD operations.

Provides reusable async database operations for all services.
"""

import uuid
from datetime import datetime
from typing import Any, Generic, Type, TypeVar

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query

from app.models.base import BaseModel
from app.services.exceptions import NotFoundError, ValidationError

# Generic type for model classes
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseService(Generic[ModelType]):
    """
    Base service providing common CRUD operations.

    Type Parameters:
        ModelType: SQLAlchemy model class extending BaseModel

    All methods are async and use AsyncSession for database operations.
    Includes soft delete support and pagination utilities.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize base service.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def get_by_id(
        self,
        id: uuid.UUID,
        include_deleted: bool = False,
        raise_if_not_found: bool = True,
    ) -> ModelType | None:
        """
        Get a single record by ID.

        Args:
            id: Record UUID
            include_deleted: Whether to include soft-deleted records
            raise_if_not_found: Whether to raise NotFoundError if not found

        Returns:
            Model instance or None if not found

        Raises:
            NotFoundError: If record not found and raise_if_not_found=True
        """
        query = select(self.model).where(self.model.id == id)

        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        result = await self.session.execute(query)
        instance = result.scalar_one_or_none()

        if instance is None and raise_if_not_found:
            raise NotFoundError(self.model.__name__, str(id))

        return instance

    async def get_all(
        self,
        include_deleted: bool = False,
        order_by: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """
        Get all records matching criteria.

        Args:
            include_deleted: Whether to include soft-deleted records
            order_by: Field name to order by (default: created_at)
            filters: Field-value pairs to filter by

        Returns:
            List of model instances
        """
        query = select(self.model)

        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))
        else:
            query = query.order_by(self.model.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        include_deleted: bool = False,
        order_by: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Get paginated records.

        Args:
            page: Page number (1-indexed)
            page_size: Number of records per page
            include_deleted: Whether to include soft-deleted records
            order_by: Field name to order by
            filters: Field-value pairs to filter by

        Returns:
            Dictionary with:
                - items: List of model instances
                - total: Total record count
                - page: Current page number
                - page_size: Records per page
                - total_pages: Total number of pages
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        if page_size > 100:
            page_size = 100

        query = select(self.model)

        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        # Count total records
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))
        else:
            query = query.order_by(self.model.created_at.desc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = list(result.scalars().all())

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def create(
        self,
        data: dict[str, Any],
        user_id: uuid.UUID | None = None,
    ) -> ModelType:
        """
        Create a new record.

        Args:
            data: Field-value pairs for the new record
            user_id: User ID for audit trail

        Returns:
            Created model instance

        Raises:
            ValidationError: If data validation fails
        """
        try:
            instance = self.model(**data)

            if user_id and hasattr(instance, "created_by_id"):
                instance.created_by_id = user_id
                instance.updated_by_id = user_id

            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)

            return instance
        except Exception as e:
            raise ValidationError(f"Failed to create {self.model.__name__}: {str(e)}")

    async def update(
        self,
        id: uuid.UUID,
        data: dict[str, Any],
        user_id: uuid.UUID | None = None,
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            id: Record UUID
            data: Field-value pairs to update
            user_id: User ID for audit trail

        Returns:
            Updated model instance

        Raises:
            NotFoundError: If record not found
            ValidationError: If data validation fails
        """
        instance = await self.get_by_id(id)

        try:
            for field, value in data.items():
                if hasattr(instance, field) and field not in ("id", "created_at", "created_by_id"):
                    setattr(instance, field, value)

            if user_id and hasattr(instance, "updated_by_id"):
                instance.updated_by_id = user_id
                instance.updated_at = datetime.utcnow()

            await self.session.flush()
            await self.session.refresh(instance)

            return instance
        except Exception as e:
            raise ValidationError(f"Failed to update {self.model.__name__}: {str(e)}")

    async def delete(self, id: uuid.UUID) -> bool:
        """
        Hard delete a record (permanent removal).

        Args:
            id: Record UUID

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If record not found
        """
        instance = await self.get_by_id(id, include_deleted=True)
        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def soft_delete(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> ModelType:
        """
        Soft delete a record (mark as deleted).

        Args:
            id: Record UUID
            user_id: User ID for audit trail

        Returns:
            Soft-deleted model instance

        Raises:
            NotFoundError: If record not found
        """
        instance = await self.get_by_id(id)

        if hasattr(instance, "deleted_at"):
            instance.deleted_at = datetime.utcnow()

            if user_id and hasattr(instance, "updated_by_id"):
                instance.updated_by_id = user_id

            await self.session.flush()
            await self.session.refresh(instance)

        return instance

    async def restore(self, id: uuid.UUID) -> ModelType:
        """
        Restore a soft-deleted record.

        Args:
            id: Record UUID

        Returns:
            Restored model instance

        Raises:
            NotFoundError: If record not found
        """
        instance = await self.get_by_id(id, include_deleted=True)

        if hasattr(instance, "deleted_at"):
            instance.deleted_at = None
            await self.session.flush()
            await self.session.refresh(instance)

        return instance

    async def exists(
        self,
        filters: dict[str, Any],
        include_deleted: bool = False,
    ) -> bool:
        """
        Check if a record exists matching criteria.

        Args:
            filters: Field-value pairs to filter by
            include_deleted: Whether to include soft-deleted records

        Returns:
            True if at least one matching record exists
        """
        query = select(func.count()).select_from(self.model)

        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.session.execute(query)
        count = result.scalar_one()

        return count > 0
