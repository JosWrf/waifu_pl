from typing import Any
from src.errors import RuntimeException

from src.Lexer import Token
from src.error_handler import ErrorHandler


class Environment:
    def __init__(
        self, error_handler: ErrorHandler, outer: "Environment" = None
    ) -> None:
        self.outer = outer
        self.bindings = {}
        self.error_handler = error_handler

    def define(self, name: str, value: Any) -> None:
        self.bindings[name] = value

    def assign_at(self, name: Token, value: Any, index: int) -> None:
        if index == 0 and name.value in self.bindings:
            self.bindings[name.value] = value
            return

        self.outer.assign_at(name, value, index - 1)

    def get_value(self, name: Token) -> Any:
        if name.value in self.bindings:
            return self.bindings[name.value]

        if self.outer:
            return self.outer.get_value(name)
        else:
            raise RuntimeException(name, f"Undefined variable '{name.value}'.")

    def get_at_index(self, name: Token, index: int) -> Any:
        if index == 0 and name.value in self.bindings:
            return self.bindings[name.value]

        return self.outer.get_at_index(name, index - 1)
