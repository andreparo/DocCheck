"""
doccheck.py — a minimal and fast docstring test runner.

Scans for lines starting with '>>test:' in docstrings of functions,
classes, and methods. Evaluates each expression and asserts it is True.

Usage Example:
    from doccheck import DocCheck
    import math_utils

    checker = DocCheck(math_utils)
    checker.run()
"""

import inspect
import types


class DocCheck:
    """
    A tool to scan a python project for embedded test conditions in docstrings 
    and evaluates them to validate code correctness.

    Example:
        def add(a: int, b: int) -> int:
            '''
            Adds two numbers.
            >>test: add(2, 3) == 5
            >>test: add(-1, 1) == 0
            '''
            return a + b
    """

    # TODO allowed_inline_tags: list[str] = [">>tests:"]


    def __init__(self, module: types.ModuleType) -> None:
        """
        Initialize the DocCheck runner.

        Args:
            module (types.ModuleType): The Python module to inspect and test.
        """
        self.module: types.ModuleType = module
        self.total_tests: int = 0
        self.failed_tests: int = 0

    def _run_Test_Line(self, expression: str, context_name: str) -> None:
        """
        Evaluate a single test expression and handle its result.

        Args:
            expression (str): The Python expression to evaluate.
            context_name (str): The function/class where the test was found.
        """
        try:
            result: bool = eval(expression, self.module.__dict__)
            assert result, f"Expression evaluated False: {expression}"
        except Exception as error:
            self.failed_tests += 1
            print(f"[FAIL] {context_name}: {expression} -> {error}")
        else:
            print(f"[PASS] {context_name}: {expression}")

    def _extract_Tests(self, obj_name: str, obj: object) -> None:
        """
        Extract and run test expressions from an object's docstring.

        Args:
            obj_name (str): Name of the object being tested.
            obj (object): Function, class, or method to scan.
        """
        docstring: str | None = inspect.getdoc(obj)
        if not docstring:
            return

        for line in docstring.splitlines():
            line = line.strip()
            if not line.startswith(">>test:"):
                continue

            self.total_tests += 1
            expression: str = line[len(">>test:") :].strip()
            self._run_Test_Line(expression, obj_name)

    def _scan_Object(self, obj_name: str, obj: object) -> None:
        """
        Recursively scan functions, classes, and methods for docstring tests.
        """
        self._extract_Tests(obj_name, obj)

        if inspect.isclass(obj):
            for member_name, member_obj in inspect.getmembers(obj):
                if inspect.isfunction(member_obj) or inspect.ismethod(member_obj):
                    self._extract_Tests(f"{obj_name}.{member_name}", member_obj)

    def run(self) -> None:
        """
        Run all discovered docstring tests within the given module.
        Prints results and a summary report.
        """
        print(f"Running docstring tests in module '{self.module.__name__}'...\n")

        for obj_name, obj in inspect.getmembers(self.module):
            if inspect.isfunction(obj) or inspect.isclass(obj):
                self._scan_Object(obj_name, obj)

        print(f"\nSummary: {self.total_tests - self.failed_tests}/{self.total_tests} tests passed.")

    @classmethod
    def run_From_CLI(cls) -> None:
        """
        Command-line entry point for `python -m doccheck` or
        `python -m doccheck <module_name>`.
        Runs on the whole project if no module name is provided.
        """
        import importlib
        import importlib.util
        import pathlib
        import sys

        args = sys.argv[1:]

        # Auto-run mode: no arguments → scan the entire project
        if not args:
            project_root = pathlib.Path.cwd()
            sys.path.insert(0, str(project_root))
            python_files = list(project_root.rglob("*.py"))

            failed_total = 0
            tested_files = 0

            for file_path in python_files:
                # skip irrelevant dirs
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                if "venv" in file_path.parts or "__pycache__" in file_path.parts:
                    continue
                if "site-packages" in file_path.parts:
                    continue

                module_name = ".".join(file_path.with_suffix("").parts)
                spec = importlib.util.spec_from_file_location(module_name, str(file_path))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    try:
                        spec.loader.exec_module(module)
                    except Exception:
                        continue  # skip broken imports

                    tested_files += 1
                    checker = cls(module)
                    checker.run()
                    failed_total += checker.failed_tests

            print(f"\nDocCheck Summary: scanned {tested_files} files.")
            if failed_total:
                print(f"❌ {failed_total} docstring tests failed.")
                sys.exit(1)
            else:
                print("✅ All docstring tests passed successfully.")
            return

        # Single-module mode: same as before
        if len(args) == 1:
            module_name: str = args[0]
            module = importlib.import_module(module_name)
            cls(module).run()
        else:
            print("Usage: python -m doccheck [<module_name>]")
            sys.exit(1)


if __name__ == "__main__":
    DocCheck.run_From_CLI()

