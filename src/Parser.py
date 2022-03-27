import importlib
from abc import ABC, abstractmethod
from typing import Any, Callable, Collection, List

from src.ast import (
    AssStmt,
    Assign,
    Expr,
    ExprStmt,
    GroupingExpr,
    Literal,
    Stmt,
    Stmts,
    UnaryExpr,
    VarAccess,
)
from src.error_handler import ErrorHandler
from src.Lexer import Token, TokenType
from src.errors import UnexpectedTokenException


class Parser(ABC):
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.index = 0
        self.lookahead = self.tokens[self.index]

    @abstractmethod
    def _parse_error(self, message: str) -> None:
        pass

    def is_eof(self) -> bool:
        return self.lookahead.type == TokenType.EOF

    def advance(self) -> Token:
        if self.is_eof():
            return self.tokens[-1]
        token = self.lookahead
        self.consume()
        return token

    def consume(self) -> None:
        self.index += 1
        if not self.is_eof():
            self.lookahead = self.tokens[self.index]

    def is_type_in(self, *token_types) -> bool:
        return self.lookahead.type in token_types

    def match(self, expected_type: TokenType, message: str) -> None:
        """match() is a support method in the Parser that consumes a token T if T is the current
        lookahead token. If there is a mismatch, match() throws an exception."""
        if self.is_type_in(expected_type):
            self.consume()
        else:
            self._parse_error(message)

    @abstractmethod
    def parse(self):
        pass


def binary_node(name: str, *token_types: Collection[TokenType]):
    module = importlib.import_module("src.ast")

    def binary_node_creator(f: Callable):
        def binary_wrapper(parser: Parser):
            left = f(parser)
            while parser.is_type_in(*token_types):
                operator = parser.advance()
                left = getattr(module, name)(left, operator, f(parser))
            return left

        return binary_wrapper

    return binary_node_creator


class RecursiveDescentParser(Parser):
    def __init__(self, tokens: List[Token], error_handler: ErrorHandler) -> None:
        super().__init__(tokens)
        self.error_handler = error_handler

    def _parse_error(self, message: str, throw: bool = True) -> None:
        message = f"Line[{self.lookahead.line}]: at {self.lookahead} " + message
        self.error_handler.error(message)
        if throw:
            raise UnexpectedTokenException()

    # TODO: Add support for error recovery
    def _synchronize(self) -> None:
        """Synchronize at statement boundaries which in my case are newlines.
        Keywords starting off statements are also synchronization words."""
        sync_token = self.advance()  # toss mismatched token
        while not self.is_eof():
            if sync_token.type == TokenType.NEWLINE:
                return
            elif self.is_type_in(
                TokenType.DEF,
                TokenType.WHILE,
                TokenType.IF,
                TokenType.RETURN,
            ):
                return
            sync_token = self.advance()

    def parse(self) -> Any:
        stmts = []
        while not self.is_eof():
            stmts.append(self._declaration())
        return Stmts(stmts)

    def _declaration(self) -> Stmt:
        try:
            return self._statement()
        except UnexpectedTokenException as ue:
            self._synchronize()

    def _statement(self) -> Stmt:
        # All valid assignment targets are expressions -> parsing
        # expressions parses assignment targets
        expr = self._expression()
        if self.is_type_in(TokenType.ASSIGNMENT):
            return self._assign_stmt(expr)
        return self._expression_stmt(expr)

    def _block_stmt(self) -> List[Stmt]:
        stmts = []
        self.advance()  # Eat the colon
        self.match(TokenType.NEWLINE, "Expect newline character after colon.")
        self.match(TokenType.INDENT, "Expect indent after block creation.")
        while not self.is_type_in(TokenType.DEDENT, TokenType.EOF):
            stmts.append(self._declaration())

        self.match(TokenType.DEDENT, "Expect dedent after block end.")
        if not stmts:
            self._parse_error("Block may not be empty.", False)
        return stmts

    def _expression_stmt(self, expr: Expr) -> ExprStmt:
        message = "Expect newline character after statement."
        self.match(TokenType.NEWLINE, message)
        return ExprStmt(expr)

    def _assign_stmt(self, expr) -> AssStmt:
        if type(expr) != VarAccess:
            self._parse_error("Can't assign to this left hand side.", False)
        name = self.tokens[self.index - 1]
        self.advance()
        ass_stmt = AssStmt(name, self._assign())
        message = "Expect newline character after assignment."
        self.match(TokenType.NEWLINE, message)
        # TODO: Try to make an entry for all defined variables, functions and classes
        return ass_stmt

    def _assign(self) -> Expr:
        expr = self._expression()
        if self.is_type_in(TokenType.ASSIGNMENT):
            if type(expr) != VarAccess:
                self._parse_error("Cant't assign to this left hand side.", False)
            name = self.tokens[self.index - 1]
            self.advance()
            expr = Assign(name, self._assign())
        return expr

    def _expression(self) -> Expr:
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
        if self.is_type_in(TokenType.NIL):
            self.consume()
            return Literal(None)
        if self.is_type_in(TokenType.TRUE):
            self.consume()
            return Literal(True)
        if self.is_type_in(TokenType.FALSE):
            self.consume()
            return Literal(False)
        if self.is_type_in(TokenType.OP_PAR):
            self.consume()
            expr = self._expression()
            self.match(
                TokenType.CL_PAR, "Unclosed '('. Expected ')' after the expression."
            )
            return GroupingExpr(expr)
        if self.is_type_in(TokenType.IDENTIFIER):
            return VarAccess(self.advance())

        self._parse_error("Token can't be used in an expression.")
