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
        Command-line entry point for `python -m doccheck <module_name>`.
        """
        import importlib
        import sys

        if len(sys.argv) != 2:
            print("Usage: python -m doccheck <module_name>")
            sys.exit(1)

        module_name: str = sys.argv[1]
        module = importlib.import_module(module_name)
        cls(module).run()


if __name__ == "__main__":
    DocCheck.run_From_CLI()

