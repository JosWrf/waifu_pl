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

    def get_value(self, name: Token) -> Any:
        if not self.bindings.get(name.value, False) is False:
            return self.bindings[name.value]

        if self.outer:
            return self.outer.get_value(name)
        else:
            raise RuntimeException(name, f"Undefined variable '{name.value}'.")
