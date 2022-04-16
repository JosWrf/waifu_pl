import importlib
from abc import ABC, abstractmethod
from typing import Any, Callable, Collection, List

from src.ast import (
    AssStmt,
    Assign,
    BlockStmt,
    BreakStmt,
    CallExpr,
    ClassDecl,
    ContinueStmt,
    Expr,
    ExprStmt,
    FunctionDecl,
    GroupingExpr,
    IfStmt,
    Literal,
    ObjRef,
    PropertyAccess,
    ReturnStmt,
    SetProperty,
    Stmt,
    Stmts,
    SuperRef,
    UnaryExpr,
    VarAccess,
    WhileStmt,
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
    def _parse_error(self, message: str, throw: bool = True) -> None:
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
        self.loop_count = 0

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
                TokenType.NEWVAR,
                TokenType.CONTINUE,
                TokenType.BREAK,
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
            if self.is_type_in(TokenType.DECORATOR):
                return self._decorator()
            if self.is_type_in(TokenType.DEF):
                return self._function_decl()
            if self.is_type_in(TokenType.CLASS):
                return self._class_decl()
            return self._statement()
        except UnexpectedTokenException as ue:
            self._synchronize()

    def _class_decl(self) -> Stmt:
        self.advance()  # consume waifu token
        if not self.is_type_in(TokenType.IDENTIFIER):
            self._parse_error("Expect identifier after 'waifu'.")
        name = self.advance()

        supercls = None
        if self.is_type_in(TokenType.EXTENDS):
            supercls = self._parse_superclasses()

        self.match(TokenType.COLON, "Expect colon after waifu declaration.")
        self.match(TokenType.NEWLINE, "Expect Newline character after ':'.")
        self.match(TokenType.INDENT, "Expect indent after block creation.")

        methods = []
        while self.is_type_in(TokenType.DEF, TokenType.STATIC):
            methods.append(self._function_decl(self.is_type_in(TokenType.STATIC)))
        self.match(TokenType.DEDENT, "Expect dedent after leaving the class body.")
        return ClassDecl(name, supercls, methods)

    def _parse_superclasses(self) -> List[VarAccess]:
        self.advance()  # consume neesan token
        supercls = []
        if not self.is_type_in(TokenType.IDENTIFIER):
            self._parse_error("Expect identifier after 'neesan'.")
        supercls.append(VarAccess(self.advance()))
        while self.is_type_in(TokenType.COMMA):
            self.advance()
            if self.is_type_in(TokenType.IDENTIFIER):
                supercls.append(VarAccess(self.advance()))
            else:
                self._parse_error("Expect identifier after ',' in neesan clause.")
        return supercls

    def _function_decl(self, static: bool = False) -> Stmt:
        self.advance()  # consume desu/oppai token
        return self._function(static)

    def _function(self, static: bool = False) -> FunctionDecl:
        if not self.is_type_in(TokenType.IDENTIFIER):
            self._parse_error("Expect identifier after 'desu'.")
        name = self.advance()
        self.match(TokenType.OP_PAR, "Expect '(' after function name.")
        params = self._formal_params()
        self.match(TokenType.CL_PAR, "Expect ')' after function parameters.")
        if not self.is_type_in(TokenType.COLON):
            self._parse_error(
                "Expect ':' for block creation after function parameters."
            )
        body = self._block_stmt()
        return FunctionDecl(None, name, params, body, static)

    def _formal_params(self) -> List[Token]:
        params = []
        if not self.is_type_in(TokenType.CL_PAR):
            if not self.is_type_in(TokenType.IDENTIFIER):
                self._parse_error("Expect identifier in function parameters.")
            params.append(self.advance())
            while self.is_type_in(TokenType.COMMA):
                self.advance()
                if len(params) > 127:
                    self._parse_error("Maximum number of parameters is 127.", False)
                if not self.is_type_in(TokenType.IDENTIFIER):
                    self._parse_error("Expect identifier in function parameters.")
                params.append(self.advance())

        return params

    def _decorator(self) -> FunctionDecl:
        self.advance()  # eat @
        if not self.is_type_in(TokenType.IDENTIFIER):
            self._parse_error("Expect identifier after '@' in decorated function.")
        name = self.advance()
        self.match(TokenType.NEWLINE, "Expect newline after decorator.")
        func = self._function_decl()
        func.decorator = VarAccess(name)
        return func

    def _statement(self) -> Stmt:
        if self.is_type_in(TokenType.IF):
            return self._if_stmt()
        if self.is_type_in(TokenType.WHILE):
            return self._while_stmt()
        if self.is_type_in(TokenType.BREAK):
            return self._break_stmt()
        if self.is_type_in(TokenType.CONTINUE):
            return self._continue_stmt()
        if self.is_type_in(TokenType.RETURN):
            return self._return_stmt()
        if self.is_type_in(TokenType.NEWVAR):
            return self._new_var()

        # All valid assignment targets are expressions -> parsing
        # expressions parses assignment targets
        expr = self._expression()
        if self.is_type_in(TokenType.ASSIGNMENT):
            return self._assign_stmt(expr)
        return self._expression_stmt(expr)

    def _break_stmt(self) -> BreakStmt:
        if self.loop_count <= 0:
            self._parse_error("Can only use yamero in a loop body.", False)
        self.advance()
        self.match(TokenType.NEWLINE, "Expect newline character after yamero.")
        return BreakStmt()

    def _continue_stmt(self) -> ContinueStmt:
        if self.loop_count <= 0:
            self._parse_error("Can only use kowai in a loop body.", False)
        self.advance()
        self.match(TokenType.NEWLINE, "Expect newline character after kowai.")
        return ContinueStmt()

    def _return_stmt(self) -> ReturnStmt:
        err = self.advance()  # consume return
        expr = None
        if not self.is_type_in(TokenType.NEWLINE):
            expr = self._expression()
        self.match(TokenType.NEWLINE, "Expect newline character after return.")
        return ReturnStmt(err, expr)

    def _while_stmt(self) -> WhileStmt:
        try:
            self.loop_count += 1
            self.advance()  # eat while token
            condition = self._expression()
            if not self.is_type_in(TokenType.COLON):
                self._parse_error("Expect ':' for block creation after while.")
            block = BlockStmt(self._block_stmt())
            return WhileStmt(condition, block)
        finally:
            self.loop_count -= 1

    def _if_stmt(self) -> IfStmt:
        self.advance()  # eat if token
        condition = self._expression()
        # TODO: Prolly cleaner to match before trying to parse a block
        if not self.is_type_in(TokenType.COLON):
            self._parse_error("Expect ':' for block creation after if.")
        block = BlockStmt(self._block_stmt())

        alternative = None
        if self.is_type_in(TokenType.ELSE):
            self.advance()
            if not self.is_type_in(TokenType.COLON):
                self._parse_error("Expect ':' for block creation after else.")
            alternative = BlockStmt(self._block_stmt())

        return IfStmt(condition, block, alternative)

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

    def _assign_stmt(self, expr: Expr, new_var: bool = False) -> Stmt:
        """Wraps a sequence of assignment expressions in a statement form. If called
        from the new_var method, assignments correspond to variable definitions.
        Feels somewhat weird to separate assignments like this."""
        self.advance()
        if type(expr) is VarAccess:
            ass_stmt = AssStmt(new_var, expr.name, self._assign(new_var))
            message = "Expect newline character after assignment."
            self.match(TokenType.NEWLINE, message)
            return ass_stmt
        elif type(expr) is PropertyAccess:
            if new_var:
                self._parse_error("Can't use 'baka' when setting properties.", False)
            setter = SetProperty(expr.obj, expr.name, self._assign(new_var))
            message = "Expect newline character after setting a property."
            self.match(TokenType.NEWLINE, message)
            return setter
        else:
            self._parse_error("Can't assign to this left hand side.", False)

    def _assign(self, new_var: bool = False) -> Expr:
        """Expression part of an assignment. Basically the same code as in _assign_stmt."""
        expr = self._expression()
        if self.is_type_in(TokenType.ASSIGNMENT):
            self.advance()
            if type(expr) is VarAccess:
                return Assign(new_var, expr.name, self._assign(new_var))
            elif type(expr) is PropertyAccess:
                return SetProperty(expr.obj, expr.name, self._assign(new_var))
            else:
                self._parse_error("Can't assign to this left hand side.", False)
                self._assign(new_var)  # Recover from error and continue parsing
        return expr

    def _new_var(self) -> AssStmt:
        """Called when baka is read, then an assignment needs to communicate
        the runtime to create a new variable in the current scope."""
        self.advance()
        expr = self._expression()
        if not self.is_type_in(TokenType.ASSIGNMENT):
            self._parse_error("Can only use 'baka' in assignments.")
        return self._assign_stmt(expr, True)

    def _expression(self) -> Expr:
        return self._lambda()

    def _lambda(self) -> Expr:
        """Instead of using a new node for lambda expressions, lambdas are desugared to function
        declarations, where the name of the function will be the empty string."""
        if self.is_type_in(TokenType.QUESTION):
            token = self.advance()
            params = (
                self._formal_params() if self.is_type_in(TokenType.IDENTIFIER) else []
            )
            self.match(TokenType.COLON, "Expect ':' after lambda expression.")
            expr = FunctionDecl(
                None,
                Token("", token.line, TokenType.IDENTIFIER),
                params,
                [ReturnStmt(token, self._lambda())],
            )
        else:
            expr = self._logic_or()
        return expr

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
        expr = self._primary()
        while self.is_type_in(TokenType.OP_PAR, TokenType.DOT):
            if self.is_type_in(TokenType.OP_PAR):
                expr = self._handle_call(expr)
            else:
                expr = self._handle_property_acc(expr)
        return expr

    def _handle_call(self, expr: Expr) -> CallExpr:
        self.advance()  # consume (
        args = self._actual_params()
        # The token does not really matter, it's only for error messages anyways
        expr = CallExpr(expr, self.lookahead, args)
        self.match(TokenType.CL_PAR, "Expected ')' after function call.")
        return expr

    def _handle_property_acc(self, expr: Expr) -> PropertyAccess:
        self.advance()  # consume dot
        name = self.lookahead
        self.match(TokenType.IDENTIFIER, "Expect identifier after '.'.")
        return PropertyAccess(expr, name)

    def _actual_params(self) -> List[Expr]:
        args = []
        if not self.is_type_in(TokenType.CL_PAR):
            args.append(self._expression())
            while self.is_type_in(TokenType.COMMA):
                self.advance()
                args.append(self._expression())

        if len(args) > 127:
            self._parse_error("Max number of arguments is 127.", False)
        return args

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
        if self.is_type_in(TokenType.THIS):
            return ObjRef(self.advance())
        if self.is_type_in(TokenType.SUPER):
            sup = self.advance()
            self.match(TokenType.DOT, "Expect '.' after 'haha'.")
            if not self.is_type_in(TokenType.IDENTIFIER):
                self._parse_error("Expect identifier after 'haha.'.")
            return SuperRef(sup, self.advance())

        self._parse_error("Token can't be used in an expression.")
