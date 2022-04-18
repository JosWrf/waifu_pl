from src.environment import Environment
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.waifu_interpreter import WaifuInterpreter


class SourceFile:
    """Stores the buffered text of a module and its absolute path."""

    def __init__(self, path: str, text: str) -> None:
        self.path = path
        self.text = text


class Module:
    """Saves identifiers and their values that can be exported into other
    modules."""

    def __init__(
        self, name: str, sourcefile: SourceFile, waifu: "WaifuInterpreter"
    ) -> None:
        self.name = name
        self.sourcefile = sourcefile
        self.exportable_vars = (
            set()
        )  # top-lvl vars that can be exported from one module
        self.scope = Environment()  # top-lvl scope of the module
        self.waifu_interpreter = (
            waifu  # this is later needed by the tree-walk-interpreter
        )

    def import_name(self, name: str, module: "Module") -> None:
        self.scope.define(name, module.scope.get(name))
