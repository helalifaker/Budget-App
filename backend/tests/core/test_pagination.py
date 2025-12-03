"""
Tests for pagination utilities.

Covers:
- PaginationParams validation
- PaginatedResponse model
- create_paginated_response helper function
- Edge cases (empty lists, boundary values)
"""

import pytest
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    create_paginated_response,
)


class TestPaginationParams:
    """Test PaginationParams model."""

    def test_default_values(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 50

    def test_custom_values(self):
        """Test custom pagination parameters."""
        params = PaginationParams(page=2, page_size=25)
        assert params.page == 2
        assert params.page_size == 25

    def test_minimum_page(self):
        """Test that page must be >= 1."""
        with pytest.raises(ValueError):
            PaginationParams(page=0)

        with pytest.raises(ValueError):
            PaginationParams(page=-1)

    def test_minimum_page_size(self):
        """Test that page_size must be >= 1."""
        with pytest.raises(ValueError):
            PaginationParams(page_size=0)

        with pytest.raises(ValueError):
            PaginationParams(page_size=-1)

    def test_maximum_page_size(self):
        """Test that page_size must be <= 100."""
        with pytest.raises(ValueError):
            PaginationParams(page_size=101)

        # Should work at boundary
        params = PaginationParams(page_size=100)
        assert params.page_size == 100


class TestPaginatedResponse:
    """Test PaginatedResponse model."""

    def test_basic_response(self):
        """Test creating a basic paginated response."""
        items = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        response = PaginatedResponse(
            items=items,
            total=100,
            page=1,
            page_size=50,
            total_pages=2,
        )

        assert len(response.items) == 2
        assert response.total == 100
        assert response.page == 1
        assert response.page_size == 50
        assert response.total_pages == 2

    def test_empty_response(self):
        """Test paginated response with no items."""
        response = PaginatedResponse(
            items=[],
            total=0,
            page=1,
            page_size=50,
            total_pages=0,
        )

        assert len(response.items) == 0
        assert response.total == 0
        assert response.total_pages == 0

    def test_last_page(self):
        """Test paginated response for last page."""
        items = [{"id": 51}, {"id": 52}]
        response = PaginatedResponse(
            items=items,
            total=52,
            page=2,
            page_size=50,
            total_pages=2,
        )

        assert len(response.items) == 2
        assert response.page == 2
        assert response.total_pages == 2

    def test_single_page(self):
        """Test paginated response when all items fit on one page."""
        items = [{"id": i} for i in range(1, 11)]
        response = PaginatedResponse(
            items=items,
            total=10,
            page=1,
            page_size=50,
            total_pages=1,
        )

        assert len(response.items) == 10
        assert response.total_pages == 1

    def test_generic_type_parameter(self):
        """Test that PaginatedResponse works with generic types."""
        from typing import List

        class UserResponse:
            def __init__(self, id: int, name: str):
                self.id = id
                self.name = name

        users = [UserResponse(1, "Alice"), UserResponse(2, "Bob")]
        response = PaginatedResponse[UserResponse](
            items=users,
            total=2,
            page=1,
            page_size=50,
            total_pages=1,
        )

        assert len(response.items) == 2
        assert response.items[0].name == "Alice"


class TestCreatePaginatedResponse:
    """Test create_paginated_response helper function."""

    def test_basic_pagination(self):
        """Test creating paginated response with basic data."""
        items = [{"id": i} for i in range(1, 51)]
        response = create_paginated_response(
            items=items,
            total=100,
            page=1,
            page_size=50,
        )

        assert len(response.items) == 50
        assert response.total == 100
        assert response.page == 1
        assert response.page_size == 50
        assert response.total_pages == 2

    def test_total_pages_calculation(self):
        """Test total_pages calculation."""
        # Exactly divisible
        response = create_paginated_response(
            items=[{"id": 1}],
            total=100,
            page=1,
            page_size=50,
        )
        assert response.total_pages == 2

        # Not exactly divisible
        response = create_paginated_response(
            items=[{"id": 1}],
            total=101,
            page=1,
            page_size=50,
        )
        assert response.total_pages == 3  # 101 / 50 = 2.02 -> 3 pages

        # Single page
        response = create_paginated_response(
            items=[{"id": 1}],
            total=10,
            page=1,
            page_size=50,
        )
        assert response.total_pages == 1

    def test_empty_items(self):
        """Test paginated response with empty items list."""
        response = create_paginated_response(
            items=[],
            total=0,
            page=1,
            page_size=50,
        )

        assert len(response.items) == 0
        assert response.total == 0
        assert response.total_pages == 0

    def test_zero_page_size(self):
        """Test paginated response with zero page_size."""
        response = create_paginated_response(
            items=[],
            total=100,
            page=1,
            page_size=0,
        )

        assert response.total_pages == 0

    def test_last_page_partial(self):
        """Test last page with partial items."""
        items = [{"id": 51}, {"id": 52}]
        response = create_paginated_response(
            items=items,
            total=52,
            page=2,
            page_size=50,
        )

        assert len(response.items) == 2
        assert response.total_pages == 2

    def test_page_size_larger_than_total(self):
        """Test when page_size is larger than total items."""
        items = [{"id": i} for i in range(1, 11)]
        response = create_paginated_response(
            items=items,
            total=10,
            page=1,
            page_size=100,
        )

        assert len(response.items) == 10
        assert response.total_pages == 1

    def test_items_count_mismatch(self):
        """Test when items list doesn't match page_size."""
        # This is a valid scenario - last page might have fewer items
        items = [{"id": 1}, {"id": 2}]
        response = create_paginated_response(
            items=items,
            total=52,
            page=2,
            page_size=50,
        )

        assert len(response.items) == 2
        assert response.total == 52
        assert response.total_pages == 2


class TestPaginationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_total(self):
        """Test pagination with very large total."""
        response = create_paginated_response(
            items=[{"id": 1}],
            total=1_000_000,
            page=1,
            page_size=50,
        )

        assert response.total_pages == 20_000  # 1,000,000 / 50

    def test_single_item(self):
        """Test pagination with single item."""
        items = [{"id": 1}]
        response = create_paginated_response(
            items=items,
            total=1,
            page=1,
            page_size=1,
        )

        assert len(response.items) == 1
        assert response.total == 1
        assert response.total_pages == 1

    def test_page_size_one(self):
        """Test pagination with page_size of 1."""
        items = [{"id": 1}]
        response = create_paginated_response(
            items=items,
            total=5,
            page=1,
            page_size=1,
        )

        assert len(response.items) == 1
        assert response.total_pages == 5

    def test_rounding_edge_case(self):
        """Test edge case where total is just below page_size boundary."""
        # 99 items with page_size 50 = 2 pages
        response = create_paginated_response(
            items=[{"id": 1}],
            total=99,
            page=1,
            page_size=50,
        )

        assert response.total_pages == 2

        # 100 items with page_size 50 = 2 pages
        response = create_paginated_response(
            items=[{"id": 1}],
            total=100,
            page=1,
            page_size=50,
        )

        assert response.total_pages == 2

        # 101 items with page_size 50 = 3 pages
        response = create_paginated_response(
            items=[{"id": 1}],
            total=101,
            page=1,
            page_size=50,
        )

        assert response.total_pages == 3

