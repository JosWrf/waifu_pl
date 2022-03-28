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

    def define(self, name: Token, value: Any) -> None:
        self.bindings[name.value] = value

    def assign(self, name: Token, value: Any) -> None:
        if not self._contains_name(name):
            self.define(name, value)
        else:
            self._assign_outer(name, value)

    def _assign_outer(self, name: Token, value: Any) -> None:
        if name.value in self.bindings:
            self.bindings[name.value] = value
            return
        return self.outer.assign(name, value)

    def _contains_name(self, name: Token) -> bool:
        if name.value in self.bindings:
            return True
        if self.outer:
            return self.outer._contains_name(name)
        else:
            return False

    def get_value(self, name: Token) -> Any:
        if name.value in self.bindings:
            return self.bindings[name.value]

        if self.outer:
            return self.outer.get_value(name)
        else:
            raise RuntimeException(name, f"Undefined variable '{name.value}'.")
