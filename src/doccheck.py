import inspect
import types
import sys
import importlib.util
import pathlib


class DocCheck:
    """
    A tool to scan a python project for embedded test conditions in docstrings
    and evaluates them to validate code correctness.

    Example:
        def add(a: int, b: int) -> int:
            '''
            Adds two numbers.
            >>test: (2 + 3) == 5
            >>test: (-1 + 1) == 0
            '''
            return a + b
    """

    def __init__(self, module: types.ModuleType) -> None:
        self.module: types.ModuleType = module
        self.total_tests: int = 0
        self.failed_tests: int = 0

    def _run_Test_Line(self, expression: str, context_name: str) -> None:
        print(f"TESTING : {expression}")
        try:
            result: bool = eval(expression, self.module.__dict__)
            assert result, f"Expression evaluated False: {expression}"
        except Exception as error:
            self.failed_tests += 1
            print(f"[FAIL] {context_name}: {expression} -> {error}")
        else:
            print(f"[PASS] {context_name}: {expression}")

    def _extract_Tests(self, obj_name: str, obj: object) -> None:
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
        self._extract_Tests(obj_name, obj)
        if inspect.isclass(obj):
            for member_name, member_obj in inspect.getmembers(obj):
                if inspect.isfunction(member_obj) or inspect.ismethod(member_obj):
                    self._extract_Tests(f"{obj_name}.{member_name}", member_obj)

    def run(self) -> None:
        print(f"Running docstring tests in module '{self.module.__name__}'...\n")
        for obj_name, obj in inspect.getmembers(self.module):
            if inspect.isfunction(obj) or inspect.isclass(obj):
                self._scan_Object(obj_name, obj)
        print(f"\nSummary: {self.total_tests - self.failed_tests}/{self.total_tests} tests passed.")

    # -------------------------------
    # ✅ SAFE MODULE LOADING UTILITIES
    # -------------------------------

    @staticmethod
    def _safe_Load_Module(file_path: pathlib.Path, module_name: str) -> types.ModuleType | None:
        """
        Load a module safely without triggering __main__ blocks or top-level code.
        Returns the loaded module or None if it cannot be imported.
        """
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            module.__name__ = f"{module_name}"
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module

        except Exception as err:
            print(f"[WARN] Skipping {file_path}: {err}")
            return None

    # -------------------------------
    # ✅ CLI ENTRY POINT
    # -------------------------------

    @classmethod
    def run_From_CLI(cls) -> None:
        """
        Command-line entry point for `python -m doccheck` or
        `python -m doccheck <module_name>` or `python -m doccheck src/`.
        Runs on the whole project if no module name is provided.
        """
        print("\n Starting doccheck from CLI: ...")

        args = sys.argv[1:]
        project_root = pathlib.Path.cwd()

        # handle "src/" case explicitly
        if args and args[0].rstrip("/\\") == "src":
            src_path = project_root / "src"
            if not src_path.exists() or not src_path.is_dir():
                print(f"[ERROR] 'src/' directory not found at {src_path}")
                sys.exit(1)

            print(f"Switching to 'src/' directory: {src_path}")
            sys.path.insert(0, str(src_path))
            project_root = src_path
            args = args[1:]  # consume "src" argument

        sys.path.insert(0, str(project_root))

        # Auto-run mode (no specific module given)
        if not args:
            python_files = list(project_root.rglob("*.py"))
            failed_total = 0
            tested_files = 0

            for file_path in python_files:
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                if any(skip in file_path.parts for skip in ("venv", "__pycache__", "site-packages")):
                    continue
                if file_path.name == "sandbox.py":
                    continue

                module_name = ".".join(file_path.with_suffix("").relative_to(project_root).parts)
                module = cls._safe_Load_Module(file_path, module_name)
                if not module:
                    continue

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
                sys.exit(1)
            return

        # Single-module mode
        if len(args) == 1:
            module_name: str = args[0]
            try:
                file_path = project_root.joinpath(*module_name.split(".")).with_suffix(".py")
                if not file_path.exists():
                    raise FileNotFoundError(f"No such module file: {file_path}")
                module = cls._safe_Load_Module(file_path, module_name)
                if not module:
                    raise ImportError(f"Failed to load {module_name}")
                cls(module).run()
            except Exception as err:
                print(f"[ERROR] {err}")
                sys.exit(1)
        else:
            print("Usage: python -m doccheck [src/] [<module_name>]")
            sys.exit(1)


if __name__ == "__main__":
    DocCheck.run_From_CLI()
