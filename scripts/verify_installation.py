#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alaya v3.0 Installation Verification Script

This script verifies that all subskills are correctly installed and
checks for common configuration issues.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple

# Force UTF-8 output for Windows compatibility
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def check_file_exists(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists and return status with message."""
    if path.exists():
        return True, f"✓ {description} found"
    else:
        return False, f"✗ {description} missing"


def check_directory_structure(root: Path) -> List[Tuple[bool, str]]:
    """Check core directory structure."""
    results = []

    # Core directories
    dirs_to_check = [
        ("scripts", "Python scripts directory"),
        ("manas", "Default personas directory"),
        ("templates", "Import templates directory"),
        ("config", "Default configuration directory"),
        ("examples", "Example knowledge base"),
        ("skills", "Subskills directory"),
    ]

    for dir_name, description in dirs_to_check:
        path = root / dir_name
        if path.exists() and path.is_dir():
            results.append((True, f"✓ {description} exists"))
        else:
            results.append((False, f"✗ {description} missing"))

    # Core files
    files_to_check = [
        ("SKILL.md", "Main skill file"),
        ("SKILL_GUIDE.md", "Operation guide"),
        ("SKILL_REF.md", "Reference documentation"),
        ("SKILL_FULL.md", "Merged skill file"),
        ("CHANGELOG.md", "Changelog"),
        ("README.md", "Project README"),
        ("LICENSE", "License file"),
    ]

    for file_name, description in files_to_check:
        path = root / file_name
        results.append(check_file_exists(path, description))

    return results


def check_subskills(root: Path) -> List[Tuple[bool, str]]:
    """Check subskill installation."""
    results = []

    subskills = [
        ("alaya-retrieval", "2.0.0"),
        ("alaya-memory", "1.0.0"),
        ("alaya-persona", "1.7.0"),
        ("alaya-import", "1.0.0"),
        ("alaya-maintenance", "1.0.0"),
    ]

    for subskill_name, expected_version in subskills:
        subskill_path = root / "skills" / subskill_name / "SKILL.md"

        if not subskill_path.exists():
            results.append((False, f"✗ {subskill_name} subskill missing"))
            continue

        # Read and check version
        try:
            with open(subskill_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if f"version: {expected_version}" in content:
                    results.append((True, f"✓ {subskill_name} v{expected_version} installed"))
                else:
                    results.append((False, f"⚠ {subskill_name} version mismatch (expected {expected_version})"))
        except Exception as e:
            results.append((False, f"✗ {subskill_name} error reading: {e}"))

    return results


def check_scripts(root: Path) -> List[Tuple[bool, str]]:
    """Check Python scripts availability."""
    results = []

    scripts = [
        ("setup_wizard.py", "Setup wizard"),
        ("build_index.py", "Index builder"),
        ("perfume.py", "Xunxi orchestrator"),
        ("import_paper.py", "Paper import"),
        ("batch_import.py", "Batch import"),
        ("health_check.py", "Health check"),
        ("fix_links.py", "Link fixer"),
        ("bi_observer.py", "BI observer"),
    ]

    for script_name, description in scripts:
        script_path = root / "scripts" / script_name
        results.append(check_file_exists(script_path, f"{description} ({script_name})"))

    return results


def check_default_personas(root: Path) -> List[Tuple[bool, str]]:
    """Check default persona files."""
    results = []

    personas = [
        "feynman",
        "buddha",
        "zhuangzi",
        "socrates",
        "carl_jung",
        "galileo",
        "audrey_hepburn",
        "xiaozhao",
    ]

    for persona_name in personas:
        json_path = root / "manas" / f"{persona_name}.json"
        md_path = root / "manas" / f"{persona_name}_profile.md"

        if json_path.exists() and md_path.exists():
            results.append((True, f"✓ {persona_name} persona complete"))
        elif json_path.exists():
            results.append((True, f"⚠ {persona_name} persona JSON only (profile.md missing)"))
        else:
            results.append((False, f"✗ {persona_name} persona missing"))

    return results


def print_results(results: List[Tuple[bool, str]], title: str):
    """Print check results with summary."""
    print(f"\n{title}")
    print("=" * 60)

    passed = sum(1 for result, _ in results if result)
    failed = sum(1 for result, _ in results if not result)
    warned = sum(1 for result, msg in results if not result and msg.startswith("⚠"))

    for result, message in results:
        print(message)

    print("-" * 60)
    print(f"Summary: {passed} passed, {warned} warnings, {failed} failed")
    print()


def main():
    """Main verification function."""
    print("Alaya v3.0 Installation Verification")
    print("=" * 60)

    # Get project root
    root = Path(__file__).parent.parent.absolute()

    print(f"Checking installation at: {root}")
    print()

    # Run checks
    all_results = []

    # 1. Directory structure
    dir_results = check_directory_structure(root)
    print_results(dir_results, "1. Directory Structure")
    all_results.extend(dir_results)

    # 2. Subskills
    subskill_results = check_subskills(root)
    print_results(subskill_results, "2. Subskills")
    all_results.extend(subskill_results)

    # 3. Scripts
    script_results = check_scripts(root)
    print_results(script_results, "3. Python Scripts")
    all_results.extend(script_results)

    # 4. Default personas
    persona_results = check_default_personas(root)
    print_results(persona_results, "4. Default Personas")
    all_results.extend(persona_results)

    # Overall summary
    total_passed = sum(1 for result, _ in all_results if result)
    total_failed = sum(1 for result, _ in all_results if not result)

    print("=" * 60)
    print(f"Overall: {total_passed}/{len(all_results)} checks passed")

    if total_failed == 0:
        print("\n✓ Installation verified successfully!")
        print("\nNext steps:")
        print("  1. Run: 'alaya init' to initialize your knowledge base")
        print("  2. Run: 'health check' to verify system health")
        return 0
    else:
        print(f"\n✗ Installation has {total_failed} issues")
        print("\nTroubleshooting:")
        print("  1. Ensure you cloned the complete repository")
        print("  2. Check that all subdirectories were created")
        print("  3. Verify file permissions")
        print("  4. Try re-running: git clone --depth 1 <repo-url>")
        return 1


if __name__ == "__main__":
    sys.exit(main())
