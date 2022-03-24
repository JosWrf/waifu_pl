from abc import ABC, abstractmethod
from typing import List
from src.Lexer import Token, TokenType
from src.error_handler import ErrorHandler


class UnexpectedTokenException(Exception):
    pass


class Parser(ABC):
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.index = 0
        self.lookahead = self.tokens[self.index]

    def advance(self) -> Token:
        if self.lookahead.type == TokenType.EOF:
            return self.lookahead[-1]
        token = self.lookahead
        self.consume()
        return token

    def consume(self) -> None:
        self.index += 1
        if self.lookahead.type != TokenType.EOF:
            self.lookahead = self.tokens[self.index]

    def is_type_in(self, *token_types) -> bool:
        return self.lookahead.type in token_types

    def match(self, expected_type: TokenType) -> None:
        """match() is a support method in the Parser that consumes a token T if T is the current
        lookahead token. If there is a mismatch, match() throws an exception."""
        if self.lookahead.type == expected_type:
            self.consume()
        else:
            raise UnexpectedTokenException()

    @abstractmethod
    def parse(self):
        pass


class RecursiveDescentParser(Parser):
    def __init__(self, tokens: List[Token], error_handler: ErrorHandler) -> None:
        super().__init__(tokens)
        self.error_handler = error_handler

    def _parse_error(self) -> None:
        # TODO: Add error messages
        message = ""
        self.error_handler.error(message)

    # TODO: Add support for error recovery
    def _synchronize(self) -> None:
        pass

    def parse(self) -> None:
        self._expression()

    def _expression(self) -> None:
        self._assignment()

    def _assignment(self) -> None:
        pass

    def _logic_or(self) -> None:
        pass

    def _logic_and(self) -> None:
        pass

    def _equality(self) -> None:
        pass

    def _comparison(self) -> None:
        pass

    def _term(self) -> None:
        pass

    def _factor(self) -> None:
        pass

    def _unary(self) -> None:
        pass

    def _call(self) -> None:
        pass

    def _primary(self) -> None:
        pass
