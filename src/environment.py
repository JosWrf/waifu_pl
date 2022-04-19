from typing import Any

from src.Lexer import Token


class Environment:
    def __init__(self, outer: "Environment" = None) -> None:
        self.outer = outer
        self.bindings = {}

    def get(self, name: str) -> Any:
        return self.bindings[name]

    def search_name(self, name: str) -> bool:
        if name in self.bindings:
            return True
        if self.outer:
            return self.outer.search_name(name)
        return False

    def define(self, name: str, value: Any) -> None:
        self.bindings[name] = value

    def assign_at(self, value: Any, scope: int, name: str) -> None:
        if scope == 0:
            self.bindings[name] = value
            return

        self.outer.assign_at(value, scope - 1, name)

    def get_at_index(self, scope: int, name: str) -> Any:
        if scope == 0:
            return self.bindings[name]

        return self.outer.get_at_index(scope - 1, name)
