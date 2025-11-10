#!/usr/bin/env python3
"""
Runs DocCheck across an entire Python project.

Automatically discovers and tests all importable Python modules
in the current working directory (typically your repo root).
Intended for use in pre-commit.
"""

from doccheck import DocCheck
import importlib.util
import pathlib
import sys


def import_module_from_path(module_path: pathlib.Path):
    """Dynamically import a Python module from a file path."""
    relative_path = module_path.relative_to(pathlib.Path.cwd())
    module_name = ".".join(relative_path.with_suffix("").parts)
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None


def main() -> None:
    project_root = pathlib.Path.cwd()
    sys.path.insert(0, str(project_root))

    python_files = list(project_root.rglob("*.py"))
    failed_total = 0
    tested_files = 0

    for file_path in python_files:
        # Skip hidden, venv, or pre-commit system dirs
        if any(part.startswith(".") for part in file_path.parts):
            continue
        if "venv" in file_path.parts or "__pycache__" in file_path.parts:
            continue
        if "site-packages" in file_path.parts:
            continue

        module = import_module_from_path(file_path)
        if not module:
            continue

        tested_files += 1
        checker = DocCheck(module)
        checker.run()
        failed_total += checker.failed_tests

    print(f"\nDocCheck Summary: scanned {tested_files} files.")
    if failed_total:
        print(f"❌ {failed_total} docstring tests failed.")
        sys.exit(1)
    else:
        print("✅ All docstring tests passed successfully.")


if __name__ == "__main__":
    main()
