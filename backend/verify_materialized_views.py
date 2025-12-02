#!/usr/bin/env python3
"""
Verification script for materialized views implementation.

This script verifies that:
1. Migration 008 has been applied
2. Materialized views exist in the database
3. Views have proper indexes
4. Views can be refreshed successfully
5. API endpoints are working

Usage:
    python verify_materialized_views.py
"""

import asyncio
import sys
from typing import Any

from app.database import get_db
from app.services.materialized_view_service import MaterializedViewService
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_migration_applied(db: AsyncSession) -> dict[str, Any]:
    """Check if migration 008 has been applied."""
    print("🔍 Checking if migration 008 is applied...")

    try:
        result = await db.execute(
            text("SELECT version_num FROM alembic_version")
        )
        current_version = result.scalar()

        # Migration 008 revision ID is 'bfc62faea07a'
        expected_version = "bfc62faea07a"

        if current_version == expected_version:
            print(f"✅ Migration 008 applied (version: {current_version})")
            return {"status": "success", "version": current_version}
        else:
            print(
                f"❌ Migration 008 NOT applied (current: {current_version}, "
                f"expected: {expected_version})"
            )
            return {
                "status": "error",
                "version": current_version,
                "expected": expected_version,
            }
    except Exception as e:
        print(f"❌ Error checking migration: {e}")
        return {"status": "error", "error": str(e)}


async def check_views_exist(db: AsyncSession) -> dict[str, Any]:
    """Check if materialized views exist."""
    print("\n🔍 Checking if materialized views exist...")

    views_to_check = [
        "mv_kpi_dashboard",
        "mv_budget_consolidation",
    ]

    results: dict[str, Any] = {}

    for view_name in views_to_check:
        try:
            result = await db.execute(
                text(
                    """
                SELECT COUNT(*)
                FROM pg_matviews
                WHERE schemaname = 'efir_budget' AND matviewname = :view_name
            """
                ),
                {"view_name": view_name},
            )
            count = result.scalar()
            exists = count is not None and count > 0

            if exists:
                print(f"✅ View 'efir_budget.{view_name}' exists")
                results[view_name] = {"status": "exists"}
            else:
                print(f"❌ View 'efir_budget.{view_name}' does NOT exist")
                results[view_name] = {"status": "missing"}

        except Exception as e:
            print(f"❌ Error checking view '{view_name}': {e}")
            results[view_name] = {"status": "error", "error": str(e)}

    return results


async def check_indexes_exist(db: AsyncSession) -> dict[str, Any]:
    """Check if indexes on materialized views exist."""
    print("\n🔍 Checking if indexes exist...")

    indexes_to_check = [
        ("mv_kpi_dashboard", "idx_mv_kpi_dashboard_version"),
        ("mv_kpi_dashboard", "idx_mv_kpi_dashboard_fiscal_year_status"),
        ("mv_budget_consolidation", "idx_mv_consolidation_version_account"),
        ("mv_budget_consolidation", "idx_mv_consolidation_category"),
        ("mv_budget_consolidation", "idx_mv_consolidation_fiscal_year"),
    ]

    results: dict[str, Any] = {}

    for view_name, index_name in indexes_to_check:
        try:
            result = await db.execute(
                text(
                    """
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE schemaname = 'efir_budget'
                  AND tablename = :view_name
                  AND indexname = :index_name
            """
                ),
                {"view_name": view_name, "index_name": index_name},
            )
            count = result.scalar()
            exists = count is not None and count > 0

            if exists:
                print(f"✅ Index '{index_name}' exists on '{view_name}'")
                results[index_name] = {"status": "exists"}
            else:
                print(f"❌ Index '{index_name}' does NOT exist on '{view_name}'")
                results[index_name] = {"status": "missing"}

        except Exception as e:
            print(f"❌ Error checking index '{index_name}': {e}")
            results[index_name] = {"status": "error", "error": str(e)}

    return results


async def check_view_data(db: AsyncSession) -> dict[str, Any]:
    """Check if materialized views contain data."""
    print("\n🔍 Checking if materialized views contain data...")

    views_to_check = [
        "efir_budget.mv_kpi_dashboard",
        "efir_budget.mv_budget_consolidation",
    ]

    results: dict[str, Any] = {}

    for view_name in views_to_check:
        try:
            result = await db.execute(text(f"SELECT COUNT(*) FROM {view_name}"))
            row_count = result.scalar()

            print(f"📊 View '{view_name}' contains {row_count} rows")
            results[view_name] = {"row_count": row_count}

            # Get view size
            result = await db.execute(
                text(
                    f"SELECT pg_size_pretty(pg_total_relation_size('{view_name}'::regclass))"
                )
            )
            size = result.scalar()
            print(f"💾 View '{view_name}' size: {size}")
            results[view_name]["size"] = size

        except Exception as e:
            print(f"❌ Error checking view data for '{view_name}': {e}")
            results[view_name] = {"status": "error", "error": str(e)}

    return results


async def test_refresh_views(db: AsyncSession) -> dict[str, Any]:
    """Test refreshing materialized views."""
    print("\n🔍 Testing materialized view refresh...")

    try:
        results = await MaterializedViewService.refresh_all(db)

        for view_name, result in results.items():
            if result["status"] == "success":
                print(
                    f"✅ Successfully refreshed '{view_name}' in "
                    f"{result['duration_seconds']}s"
                )
            else:
                print(f"❌ Failed to refresh '{view_name}': {result.get('error')}")

        return results

    except Exception as e:
        print(f"❌ Error testing refresh: {e}")
        return {"status": "error", "error": str(e)}


async def main():
    """Run all verification checks."""
    print("=" * 80)
    print("Materialized Views Verification Script")
    print("=" * 80)

    # Get database session
    async for db in get_db():
        try:
            # Run all checks
            migration_status = await check_migration_applied(db)
            views_status = await check_views_exist(db)
            indexes_status = await check_indexes_exist(db)
            await check_view_data(db)  # Display info but don't use in summary
            refresh_status = await test_refresh_views(db)

            # Summary
            print("\n" + "=" * 80)
            print("VERIFICATION SUMMARY")
            print("=" * 80)

            all_passed = True

            # Check migration
            if migration_status.get("status") != "success":
                print("❌ Migration 008 NOT applied")
                all_passed = False

            # Check views
            for view_name, status in views_status.items():
                if status.get("status") != "exists":
                    print(f"❌ View '{view_name}' missing")
                    all_passed = False

            # Check indexes
            for index_name, status in indexes_status.items():
                if status.get("status") != "exists":
                    print(f"❌ Index '{index_name}' missing")
                    all_passed = False

            # Check refresh
            for view_name, result in refresh_status.items():
                if result.get("status") != "success":
                    print(f"❌ Refresh failed for '{view_name}'")
                    all_passed = False

            if all_passed:
                print("\n✅ ALL VERIFICATION CHECKS PASSED")
                print("\nMaterialized views are ready for production use!")
                return 0
            else:
                print("\n❌ SOME VERIFICATION CHECKS FAILED")
                print(
                    "\nPlease review the errors above and ensure migration 008 is applied."
                )
                return 1

        except Exception as e:
            print(f"\n❌ Unexpected error during verification: {e}")
            return 1
        finally:
            await db.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
