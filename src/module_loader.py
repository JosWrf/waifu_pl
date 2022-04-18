import os
from src.error_handler import ErrorHandler
from src.module import SourceFile
from pathlib import Path


class ModuleLoader:
    """Loading a module consists of mapping the module name to an absolute path
    and buffering the source text.
    """

    def __init__(self, error_handler: ErrorHandler) -> None:
        self.error_handler = error_handler

    def load_module(self, module_path: str, current_module_path: str) -> SourceFile:
        """Maps the module path to an os path and reads in the
        .waifu file found if any."""
        # TODO: Establish connection between interpreter and loader, so we get our hands on the line number
        try:
            abs_path = None
            if module_path.startswith("."):
                abs_path = self._relative_import(module_path, current_module_path)
            else:
                abs_path = self._relative_to_cwd(module_path)
            return self.read_source(abs_path)
        except OSError:
            self.error_handler.error(
                f"Import error: Could not load '{module_path}' from {current_module_path}",
                True,
            )
            return None

    def _relative_import(self, module_path: str, current_module_path: str) -> str:
        """If the module name starts with . then a relative import is to
        be used. The path is calculated relative to the importing file."""
        current = Path(current_module_path)
        index = 0
        while module_path[index] == ".":
            index += 1
        try:
            current = current.parents[index - 1]
            suffix = module_path[index:].replace(".", "/") + ".waifu"
            return os.path.normpath(os.path.join(current, suffix))
        except IndexError:  # too many dots supplied
            self.error_handler.error(
                f"'{module_path}' can not be resolved to a valid relative path for {current_module_path}.",
                True,
            )

    def _relative_to_cwd(self, module_path: str) -> str:
        """If the importing module name does not start with '.' it is assumed that the
        module name should be looked up with respect to the cwd."""
        path = module_path.replace(".", "/") + ".waifu"
        return os.path.normpath(os.path.join(os.getcwd(), path))

    def read_source(self, absolute_path: str) -> SourceFile:
        """Reads the source file and buffers its contents in a source
        file object that is returned afterwards. Returning None indicates
        a runtime error. OSErrors are propagated."""
        with open(absolute_path, "r") as f:
            buffer = f.read()
        return SourceFile(absolute_path, buffer)
