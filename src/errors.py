from src.Lexer import Token


class UnexpectedTokenException(Exception):
    pass


class RuntimeException(RuntimeError):
    def __init__(self, token: Token, message: str) -> None:
        super().__init__()
        self.token = token
        self.message = message
