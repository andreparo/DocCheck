import inspect
from types import ModuleType
import sys
import pkgutil
import importlib.util
from pathlib import Path
import os
from typing import Any
import re

"""

AVAILABLE SYNTAX


CLASS EXAMPLES: create test examples for a class

>>example1: cls(arg1, arg2, ...)
>>example2: cls(arg1, arg2, ...)

to reference:
>>test:  cls.example1.attr == foo
>>test: cls.example2.func(arg1) == foo

also referencable in another class that import the class
>>test: AnotherClass.example1 == cls.example2.get_Foo()

is it possible to assert that something cause an error
>>error: 10 /0 


"""


class DocCheck:
    """
    A tool to scan a python project for embedded test conditions in docstrings
    and evaluates them to validate code correctness.

    """

    project_path: Path | None = None
    root_package: ModuleType | None = None
    modules_list: list[ModuleType] = []
    classes_list: list[Any] = []

    @classmethod
    def load_Root_Package_From_Path(cls, project_path: str) -> None:
        """Load the root package module object from a filesystem path."""
        # Normalize and ensure absolute path
        abs_path: str = os.path.abspath(project_path)

        if not os.path.isdir(abs_path):
            raise ValueError(f"Project root Path does not exist or is not a directory: {abs_path}")

        # The package name is the folder name
        package_name: str = os.path.basename(abs_path)

        # Add parent directory to sys.path so Python can find the package
        parent_dir: str = os.path.dirname(abs_path)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        try:
            # Import the package
            cls.root_package = importlib.import_module(package_name)
            print(f"Succesfully imported root module: {package_name}")
        except Exception as err:
            print(f"Error while importing root module {package_name}: {err}")
            sys.exit(1)

    @classmethod
    def find_All_Python_Classes_From_Root_Module(cls) -> None:
        """Find all modules of a project from a root module"""

        # Walk through the package hierarchy
        for module_info in pkgutil.walk_packages(cls.root_package.__path__, cls.root_package.__name__ + "."):
            try:
                module = importlib.import_module(module_info.name)
                cls.modules_list.append(module)

                # Collect all classes defined in the current module (not imported)
                for _, class_obj in inspect.getmembers(module, inspect.isclass):
                    if not inspect.isclass(class_obj):
                        print(f"Error: impossible to load class {class_obj}: it's not a class")
                        sys.exit(1)

                    if class_obj.__module__.lower() != module_info.name.lower():
                        # print(f"Skipped: impossible to load class {class_obj}: class module is different from package name: {module_info.name}")
                        continue

                    print(f"Succesfully loaded class {class_obj}")
                    cls.classes_list.append(class_obj)

            except Exception as error:
                print(f"Error: impossible to load module {module_info.name}: {error}")
                sys.exit(1)

    @classmethod
    def load_Classes_Docstrings(cls) -> None:
        """Create in each class a new variable named _docstrings as list[str]"""

        def safe_Splitlines_Preserving_Parentheses(text: str) -> list[str]:
            """
            Split text into lines, but do not split when the newline occurs inside
            (), [] or {}. This handles nesting without regex.
            """
            result_chars: list[str] = []
            paren_depth: int = 0
            bracket_depth: int = 0
            brace_depth: int = 0

            # Walk each character; when inside any brackets, convert newline to space.
            for ch in text:
                if ch == '(':
                    paren_depth += 1
                    result_chars.append(ch)
                    continue
                if ch == ')':
                    paren_depth = max(0, paren_depth - 1)
                    result_chars.append(ch)
                    continue
                if ch == '[':
                    bracket_depth += 1
                    result_chars.append(ch)
                    continue
                if ch == ']':
                    bracket_depth = max(0, bracket_depth - 1)
                    result_chars.append(ch)
                    continue
                if ch == '{':
                    brace_depth += 1
                    result_chars.append(ch)
                    continue
                if ch == '}':
                    brace_depth = max(0, brace_depth - 1)
                    result_chars.append(ch)
                    continue

                if ch == '\n' and (paren_depth > 0 or bracket_depth > 0 or brace_depth > 0):
                    # Keep the content continuous when inside any bracket type
                    result_chars.append(' ')
                else:
                    result_chars.append(ch)

            merged_text: str = ''.join(result_chars)

            # Standard split; also strip and drop empty lines
            logical_lines: list[str] = []
            for raw_line in merged_text.splitlines():
                line: str = ' '.join(raw_line.split())  # collapse internal whitespace nicely
                if line:
                    logical_lines.append(line)
            return logical_lines

        for class_instance in cls.classes_list:
            tmp_list: list[str] = []

            class_doc = inspect.getdoc(class_instance)
            if class_doc:
                tmp_list.extend(safe_Splitlines_Preserving_Parentheses(class_doc))

            for name, member in inspect.getmembers(class_instance):
                if inspect.isfunction(member) or isinstance(member, (classmethod, staticmethod)):
                    func_obj = (
                        member
                        if inspect.isfunction(member)
                        else member.__func__  # unwrap classmethod or staticmethod
                    )
                    method_doc = inspect.getdoc(func_obj)
                    if method_doc:
                        tmp_list.extend(safe_Splitlines_Preserving_Parentheses(method_doc))


            setattr(class_instance, "_docstrings", tmp_list.copy())
            print(f"Found {len(tmp_list)} docstring lines for class {class_instance.__name__}")

    @classmethod
    def load_Classes_Examples(cls) -> bool:
        """Load for each class the example variables"""
        for class_instance in cls.classes_list:

            for doc in class_instance._docstrings:
                if ">>example" in doc:

                    match = re.search(r">>example(\d+):", doc)
                    if not match:
                        print(f"Error: example number regex match failed in class: {class_instance} and doc: {doc}")
                        sys.exit(1)

                    example_id: int = int(match.group(1))

                    payload: str = doc.split(":")[-1]

                    # Prepare a safe evaluation context
                    module_globals: dict[str, Any] = {}
                    try:
                        module_globals = sys.modules[class_instance.__module__].__dict__
                    except KeyError:
                        print(f"Warning: could not find module globals for {class_instance.__module__}")

                    # Safe eval environment includes:
                    # - the class
                    # - module-level globals (imports, constants, etc.)
                    # - common useful builtins if missing
                    eval_env: dict[str, Any] = {"cls": class_instance, class_instance.__name__: class_instance, **module_globals}

                    try:
                        example_object = eval(payload, eval_env)
                        setattr(class_instance, f"example{example_id}", example_object)
                        print(f"Loaded example{example_id} for class {class_instance.__name__}: payload: {doc}\nSUCCESS: True\n")
                    except Exception as error:
                        print(f"Error while evaluating example{example_id} for class {class_instance.__name__}: {error=} {doc=}\nSUCCESS: False\n")
                        return False

                    setattr(class_instance, f"example{example_id}", example_object)
        return True

    @classmethod
    def run_Classes_Tests(cls) -> bool:

        result: bool = True
        test_processed: int = 0

        for class_instance in cls.classes_list:

            for doc in class_instance._docstrings:
                if ">>test:" in doc or ">>error:" in doc:
                    test_processed += 1

                    payload: str = doc.split(":")[-1]

                    # Prepare a safe evaluation context
                    module_globals: dict[str, Any] = {}
                    try:
                        module_globals = sys.modules[class_instance.__module__].__dict__
                    except KeyError:
                        print(f"Warning: could not find module globals for {class_instance.__module__}")

                    # Safe eval environment includes:
                    # - the class
                    # - module-level globals (imports, constants, etc.)
                    # - common useful builtins if missing
                    eval_env: dict[str, Any] = {"cls": class_instance, class_instance.__name__: class_instance, **module_globals}

                    if ">>test:" in doc:
                        try:
                            test_result = eval(payload, eval_env)
                            print(f"Executed test in class {class_instance.__name__}, payload: {payload}\nPASSED: {test_result}\n")
                            result = result and test_result

                        except Exception as error:
                            print(f"Error while evaluating test {payload} for class {class_instance.__name__}: {error}\nPASSED: False\n")
                            result = False

                    elif ">>error:" in doc:
                        try:
                            test_result = eval(payload, eval_env)
                            print(f"Error while evaluating error test {payload} for class {class_instance.__name__}: no error trown\nPASSED: False\n")
                            result = False
                            
                        except Exception as err:
                            print(f"Executed error test in class {class_instance.__name__}, payload: {payload}\nPASSED: True\n")
                            result = True
        
        if test_processed > 0:
            return result
        else:
            print("Error: to use doccheck at least one test must pass")
            return False

    @classmethod
    def run(cls, path: str) -> bool:
        """Return if all tests passed"""
        DocCheck.load_Root_Package_From_Path(path)
        print("\n")
        DocCheck.find_All_Python_Classes_From_Root_Module()
        print("\n")
        DocCheck.load_Classes_Docstrings()
        print("\n")
        res = DocCheck.load_Classes_Examples()
        if res is False:
            return False
        print("\n")
        return DocCheck.run_Classes_Tests()
        

def main() -> None:
    """Entry point for the DocCheck CLI."""
    args: list[str] = sys.argv[1:]

    if not args:
        path = "sandbox"
    else:
        path = args[0]
    
    result: bool = DocCheck.run(path)

    print(f"returning test result: {result}")

    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()