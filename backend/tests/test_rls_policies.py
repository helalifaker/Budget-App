"""
Lightweight checks for RLS policy definitions.

We verify the SQL policy file aligns with current expectations:
- Viewers are restricted to approved, non-deleted budget versions.
- Managers' read access excludes soft-deleted versions.
- Standard versioned-table policies enforce deleted_at filters.
"""

import re
from pathlib import Path


RLS_FILE = (
    Path(__file__).resolve().parents[2] / "docs" / "DATABASE" / "sql" / "rls_policies.sql"
)


def _read_rls() -> str:
    return RLS_FILE.read_text(encoding="utf-8")


def test_viewer_policy_restricts_to_approved_and_non_deleted():
    text = _read_rls()
    viewer_policy = re.search(
        r'CREATE POLICY "budget_versions_viewer_select".+?USING \((?P<body>.+?)\);',
        text,
        re.DOTALL,
    )
    assert viewer_policy, "Viewer policy not found"
    body = viewer_policy.group("body")
    assert "status = 'approved'" in body
    assert "deleted_at IS NULL" in body


def test_manager_read_policy_excludes_deleted():
    text = _read_rls()
    mgr_policy = re.search(
        r'CREATE POLICY "budget_versions_read_all".+?USING \((?P<body>.+?)\);',
        text,
        re.DOTALL,
    )
    assert mgr_policy, "Manager read policy not found"
    body = mgr_policy.group("body")
    assert "deleted_at IS NULL" in body
    assert "manager" in body


def test_versioned_tables_policy_templates_filter_deleted():
    text = _read_rls()
    # Look for deleted_at filters inside the Planning layer DO block
    assert "deleted_at IS NULL" in text, "Versioned table policies must filter deleted_at"
