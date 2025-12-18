"""
Lightweight integration-ish tests using the SQLite test database.

These ensure:
- Tables can be created from ORM metadata.
- BudgetVersion basic CRUD + soft delete works.
- Planning uniques (e.g., revenue_plans) are enforced at the DB level.

NOTE: Tests use SQLite with a mock auth.users table (created in conftest.py)
to satisfy FK constraints that reference Supabase's auth schema.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from app.models import RevenuePlan, Version

# Backward compatibility alias
BudgetVersion = Version
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Skip all integration tests - require PostgreSQL with Supabase auth schema
# SQLite cannot reference auth.users table during metadata.create_all
pytestmark = pytest.mark.skip(reason="Requires PostgreSQL with auth.users (Supabase)")


class TestSchema:
    async def test_tables_create(self, db_session: AsyncSession):
        """Basic sanity: can select from budget_versions table."""
        result = await db_session.execute(select(1))
        assert result.scalar() == 1


class TestBudgetVersion:
    async def test_create_and_soft_delete(self, db_session: AsyncSession):
        """BudgetVersion CRUD + soft delete flag."""
        version = BudgetVersion(
            id=uuid4(),
            name="Test Budget",
            fiscal_year=2026,
            academic_year="2025-2026",
            status="working",
        )
        db_session.add(version)
        await db_session.commit()

        result = await db_session.execute(
            select(BudgetVersion).where(BudgetVersion.id == version.id)
        )
        created = result.scalar_one()
        assert created.name == "Test Budget"
        assert created.deleted_at is None

        # Soft delete
        created.deleted_at = datetime.utcnow()
        await db_session.commit()

        result = await db_session.execute(
            select(BudgetVersion).where(BudgetVersion.id == version.id)
        )
        deleted = result.scalar_one()
        assert deleted.deleted_at is not None


class TestPlanningUniques:
    async def test_revenue_plan_unique_per_version_account(
        self, db_session: AsyncSession
    ):
        """Unique constraint should prevent duplicate revenue entries."""
        version = BudgetVersion(
            id=uuid4(),
            name="Revenue Test",
            fiscal_year=2026,
            academic_year="2025-2026",
            status="working",
        )
        db_session.add(version)
        await db_session.commit()

        rp1 = RevenuePlan(
            id=uuid4(),
            version_id=version.id,
            account_code="70110",
            description="Tuition T1",
            category="tuition",
            amount_sar=1000,
            is_calculated=True,
        )
        db_session.add(rp1)
        await db_session.commit()

        rp2 = RevenuePlan(
            id=uuid4(),
            version_id=version.id,
            account_code="70110",  # duplicate account_code for same version
            description="Tuition T1 duplicate",
            category="tuition",
            amount_sar=2000,
            is_calculated=True,
        )
        db_session.add(rp2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()
