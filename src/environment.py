from typing import Any

from src.Lexer import Token
from src.error_handler import ErrorHandler


class Environment:
    # TODO: This environment should be populated with identifiers during parsing
    # Basically much like forward references
    # In the second phase, resolving should check for undefined variables
    # During interpretation values are stored for the resolved variables
    def __init__(self, error_handler: ErrorHandler) -> None:
        self.bindings = {}
        self.error_handler = error_handler

    def define(self, name: Token, value: Any) -> None:
        if self.bindings.get(name.value, False) is False:
            self.bindings[name.value] = value
        else:
            self.error_handler.error(
                f"Line[{name.line}]: Already defined variable '{name.value}'."
            )

    def get_value(self, name: Token) -> Any:
        if not self.bindings.get(name.value, False) is False:
            return self.bindings[name.value]
        else:
            self.error_handler.error(
                f"Line[{name.line}]: Undefined variable '{name.value}'."
            )

    def set_value(self, name: Token, value: Any) -> None:
        """Called by the runtime after declarations have been resolved."""
        self.bindings[name.value] = value
