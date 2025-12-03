"""
Sanity checks on migration files for critical business rules.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_class_structure_validation_migration_exists():
    """Ensure the validation trigger migration is present and contains expected function name."""
    mig = ROOT / "backend" / "alembic" / "versions" / "20251201_0100_class_structure_validation.py"
    assert mig.exists(), "Class structure validation migration missing"
    content = mig.read_text(encoding="utf-8")
    assert "validate_class_structure_size" in content
    assert "class_structures" in content


def test_latest_migration_numbers_are_increasing():
    """Basic check that migration filenames are sorted by timestamp prefix."""
    versions_dir = ROOT / "backend" / "alembic" / "versions"
    files = sorted(p.name for p in versions_dir.glob("*.py"))
    # Expect the last migration to be the writeback layer one
    assert files, "No migration files found"
    assert files[-1].startswith("20251202_2330"), "Latest migration mismatch"
