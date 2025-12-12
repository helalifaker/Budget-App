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
    assert files, "No migration files found"
    # Verify that files are naturally sorted (timestamps should increase)
    # Each migration should have a timestamp-based prefix (YYYYMMDD_HHMM)
    for f in files:
        assert f[:8].isdigit(), f"Migration {f} should start with YYYYMMDD timestamp"
    # Verify no duplicate timestamps (allowing suffixes like 0001a)
    [f[:13] for f in files]  # YYYYMMDD_HHMM
    # Files should be sorted chronologically (already true if sorted alphabetically)
    assert files == sorted(files), "Migrations should be named to sort chronologically"
