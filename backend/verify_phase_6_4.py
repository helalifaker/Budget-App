#!/usr/bin/env python3
"""
Verification script for Phase 6.4 implementation.
Checks that all files are properly created and importable.
"""

import sys
from pathlib import Path

def check_file_exists(filepath: str) -> bool:
    """Check if file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"✓ {filepath} exists ({path.stat().st_size} bytes)")
        return True
    else:
        print(f"✗ {filepath} NOT FOUND")
        return False

def check_import(module_path: str) -> bool:
    """Check if module can be imported."""
    try:
        parts = module_path.split('.')
        module = __import__(module_path)
        for part in parts[1:]:
            module = getattr(module, part)
        print(f"✓ {module_path} imports successfully")
        return True
    except Exception as e:
        print(f"✗ {module_path} import failed: {e}")
        return False

def main():
    print("=" * 70)
    print("Phase 6.4 Implementation Verification")
    print("=" * 70)
    
    all_checks_passed = True
    
    # Check files exist
    print("\n1. Checking files exist...")
    files = [
        "app/services/consolidation_service.py",
        "app/services/financial_statements_service.py",
        "app/schemas/consolidation.py",
        "app/api/v1/consolidation.py",
    ]
    
    for file in files:
        if not check_file_exists(file):
            all_checks_passed = False
    
    # Check imports
    print("\n2. Checking imports...")
    modules = [
        "app.services.consolidation_service",
        "app.services.financial_statements_service",
        "app.schemas.consolidation",
        "app.api.v1.consolidation",
    ]
    
    for module in modules:
        if not check_import(module):
            all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_checks_passed:
        print("✅ All checks passed! Phase 6.4 implementation verified.")
        print("=" * 70)
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
