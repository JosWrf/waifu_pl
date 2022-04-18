from typing import Any
from src.Lexer import Token


class UnexpectedTokenException(Exception):
    pass


class ModuleException(RuntimeError):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message


class ModuleLoaderException(ModuleException):
    pass


class CyclicDependencyException(ModuleException):
    pass


class RuntimeException(RuntimeError):
    def __init__(self, token: Token, message: str) -> None:
        super().__init__()
        self.token = token
        self.message = message


class BreakException(RuntimeException):
    def __init__(self, token: Token = None, message: str = "") -> None:
        super().__init__(token, message)


class ContinueException(RuntimeException):
    def __init__(self, token: Token = None, message: str = "") -> None:
        super().__init__(token, message)


class ReturnException(RuntimeException):
    def __init__(self, token: Token, value: Any, message: str = "") -> None:
        super().__init__(token, message)
        self.value = value
