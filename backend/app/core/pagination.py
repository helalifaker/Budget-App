"""
Pagination utilities for API responses.

Provides Pydantic models and helper functions for paginated results.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Query parameters for pagination.

    Used in FastAPI endpoints to accept pagination parameters.
    """

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=100, description="Number of items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response model.

    Type Parameters:
        T: Type of items in the response

    Example:
        ```python
        class UserResponse(BaseModel):
            id: UUID
            name: str

        response = PaginatedResponse[UserResponse](
            items=[...],
            total=100,
            page=1,
            page_size=50,
            total_pages=2
        )
        ```
    """

    items: list[T] = Field(description="List of items for current page")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 50,
                "total_pages": 2,
            }
        }


def create_paginated_response(
    items: list[T],
    total: int,
    page: int,
    page_size: int,
) -> PaginatedResponse[T]:
    """
    Create a paginated response from items and pagination metadata.

    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        page_size: Number of items per page

    Returns:
        Paginated response with metadata
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
