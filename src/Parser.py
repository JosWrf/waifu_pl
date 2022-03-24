import importlib
from abc import ABC, abstractmethod
from typing import Callable, Collection, List

from src.ast import Expr, GroupingExpr, Literal, UnaryExpr
from src.error_handler import ErrorHandler
from src.Lexer import Token, TokenType


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


def binary_node(name: str, *token_types: Collection[TokenType]):
    module = importlib.import_module("src.ast")

    def binary_node_creator(f: Callable):
        def binary_wrapper(parser: Parser):
            left = f(parser)
            while parser.lookahead.type in token_types:
                operator = parser.advance()
                left = getattr(module, name)(left, operator, f(parser))
            return left

        return binary_wrapper

    return binary_node_creator


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
        return self._expression()

    def _expression(self) -> Expr:
        return self._assignment()

    def _assignment(self) -> Expr:
        return self._logic_or()

    @binary_node("LogicalExpr", TokenType.OR)
    def _logic_or(self) -> Expr:
        return self._logic_and()

    @binary_node("LogicalExpr", TokenType.AND)
    def _logic_and(self) -> Expr:
        return self._equality()

    @binary_node("BinaryExpr", TokenType.UNEQUAL, TokenType.EQUAL)
    def _equality(self) -> Expr:
        return self._comparison()

    @binary_node(
        "BinaryExpr",
        TokenType.LESS,
        TokenType.LESS_EQ,
        TokenType.GREATER,
        TokenType.GREATER_EQ,
    )
    def _comparison(self) -> Expr:
        return self._term()

    @binary_node("BinaryExpr", TokenType.PLUS, TokenType.MINUS)
    def _term(self) -> Expr:
        return self._factor()

    @binary_node("BinaryExpr", TokenType.TIMES, TokenType.DIVIDE)
    def _factor(self) -> Expr:
        return self._unary()

    def _unary(self) -> Expr:
        if self.is_type_in(TokenType.NOT, TokenType.MINUS):
            operator = self.advance()
            return UnaryExpr(operator, self._unary())
        return self._call()

    def _call(self) -> Expr:
        return self._primary()

    def _primary(self) -> Expr:
        if self.is_type_in(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.advance().value)
        elif self.is_type_in(TokenType.NIL):
            self.consume()
            return Literal(None)
        elif self.is_type_in(TokenType.TRUE):
            self.consume()
            return Literal(True)
        elif self.is_type_in(TokenType.FALSE):
            self.consume()
            return Literal(False)
        elif self.is_type_in(TokenType.OP_PAR):
            self.consume()
            expr = self._expression()
            self.match(TokenType.CL_PAR)
            return GroupingExpr(expr)
        # TODO: ADD errorhandling when nothing matches and when ) not found.
