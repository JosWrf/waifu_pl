from abc import ABC
from typing import Any


class Visitor(ABC):
    def visit(self, node: Any) -> None:
        method_name = f"visit_{type(node).__name__.lower()}"
        return getattr(self, method_name, self.generic_visit)(node)

    def generic_visit(self, node: Any) -> None:
        print(f"{type(node.__name__)}  has no visit method.")
        raise Exception()
