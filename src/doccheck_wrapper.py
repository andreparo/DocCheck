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

    # Find all Python files recursively
    python_files = [
        path for path in project_root.rglob("*.py")
        if not any(part.startswith(".") for part in path.parts)
        and "venv" not in path.parts
        and "__pycache__" not in path.parts
        and "site-packages" not in path.parts
    ]

    total_files = len(python_files)
    print(f"\n🔍 DocCheck: preparing to scan {total_files} Python files under '{project_root.name}'...\n")

    failed_total = 0
    tested_files = 0

    for index, file_path in enumerate(python_files, start=1):
        print(f"▶️ [{index}/{total_files}] Checking '{file_path.relative_to(project_root)}'")

        module = import_module_from_path(file_path)
        if not module:
            continue

        tested_files += 1
        checker = DocCheck(module)
        checker.run()
        failed_total += checker.failed_tests

    print(f"\nDocCheck Summary: scanned {tested_files}/{total_files} files.")
    if failed_total:
        print(f"❌ {failed_total} docstring tests failed.\n")
        sys.exit(1)
    else:
        print("✅ All docstring tests passed successfully.\n")


if __name__ == "__main__":
    main()
