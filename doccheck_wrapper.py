#!/usr/bin/env python3
"""
A small wrapper to run DocCheck against project modules.
Intended for use with pre-commit.
"""

from doccheck import DocCheck
import importlib
import sys
import pathlib


def main() -> None:
    project_root = pathlib.Path(__file__).resolve().parent.parent
    src_dir = project_root / "src"  # adjust if needed (could be "." or "my_package")
    sys.path.insert(0, str(project_root))

    # List all Python modules or packages you want to scan
    modules_to_check = [
        "src.my_package",  # example; adjust as needed
        "tests",           # optional: test module docchecks
    ]

    failed_total = 0

    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            checker = DocCheck(module)
            checker.run()
            if checker.failed_tests:
                failed_total += checker.failed_tests
        except Exception as err:
            print(f"[ERROR] Failed to import {module_name}: {err}")
            failed_total += 1

    if failed_total:
        print(f"\nDocCheck failed with {failed_total} total failed tests.")
        sys.exit(1)

    print("\nAll docstring tests passed successfully.")


if __name__ == "__main__":
    main()
