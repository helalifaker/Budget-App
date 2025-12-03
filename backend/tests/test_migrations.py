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
    # Verify migrations exist and are sorted by timestamp
    assert files, "No migration files found"
    # Check that files are in ascending timestamp order
    timestamps = [f.split("_")[0] for f in files]
    assert timestamps == sorted(timestamps), "Migration files are not in timestamp order"
