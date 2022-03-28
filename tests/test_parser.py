from typing import Any, List, Tuple
from unittest.mock import create_autospec

import pytest
from src.Lexer import Lexer, Token, TokenType
from src.Parser import RecursiveDescentParser
from src.ast import (
    AssStmt,
    Assign,
    BinaryExpr,
    BlockStmt,
    BreakStmt,
    ContinueStmt,
    Expr,
    ExprStmt,
    GroupingExpr,
    IfStmt,
    Literal,
    LogicalExpr,
    Stmt,
    Stmts,
    UnaryExpr,
    VarAccess,
    WhileStmt,
)
from src.error_handler import ErrorHandler
from src.visitor import Visitor


class ASTNodeComparator(Visitor):
    """Uses the visitor pattern to compare whether the AST constructed by the parser
    matches the expected AST."""

    def visit_assign(self, node: Assign) -> Tuple[Expr]:
        return (node.expression,)

    def visit_binaryexpr(self, node: BinaryExpr) -> Tuple[Expr, Expr]:
        return (node.left, node.right)

    def visit_unaryexpr(self, node: UnaryExpr) -> Tuple[Expr]:
        return (node.expression,)

    def visit_logicalexpr(self, node: LogicalExpr) -> Tuple[Expr, Expr]:
        return (node.left, node.right)

    def visit_literal(self, node: Literal) -> Tuple[()]:
        return ()

    def visit_varaccess(self, node: VarAccess) -> Tuple[()]:
        return ()

    def visit_groupingexpr(self, node: GroupingExpr) -> Tuple[Expr]:
        return (node.expression,)

    def visit_stmts(self, node: Stmts) -> List[Stmt]:
        return node.stmts

    def visit_blockstmt(self, node: BlockStmt) -> List[Stmt]:
        return node.stmts

    def visit_ifstmt(self, node: IfStmt) -> Tuple[Any]:
        return (
            (node.cond, node.then, node.other) if node.other else (node.cond, node.then)
        )

    def visit_whilestmt(self, node: WhileStmt) -> Tuple[Any]:
        return (node.cond, node.body)

    def visit_assstmt(self, node: AssStmt) -> Tuple[Expr]:
        return (node.expression,)

    def visit_exprstmt(self, node: ExprStmt) -> Tuple[Expr]:
        return (node.expression,)

    def visit_continuestmt(self, node: ContinueStmt) -> Tuple[()]:
        return ()

    def visit_breakstmt(self, node: BreakStmt) -> Tuple[()]:
        return ()

    def compare_nodes(self, created_node: Any, expected_node: Any) -> bool:
        """The best way to compare would be to replace the if(type) line and replace
        it with an equality comparison. This requires messing with the template, though."""
        if type(created_node) != type(expected_node) and self._check_operator(
            created_node, expected_node
        ):
            return False
        for created, expected in zip(
            self.visit(created_node), self.visit(expected_node)
        ):
            if not self.compare_nodes(created, expected):
                return False
        return True

    def _check_operator(self, node: Any, expected_node: Any) -> bool:
        """Check whether operators in binary and logical nodes are the same.
        Primary usage is to check whether operator precedence works as intended."""
        op1 = getattr(node, "operator", None)
        op2 = getattr(expected_node, "operator", None)
        return op1.type == op2.type if op1 and op2 else True


class TestParser:
    def _setup(self, text: str) -> None:
        self.comparator = ASTNodeComparator()
        self.error_handler = create_autospec(ErrorHandler)
        self.lexer = Lexer(text, self.error_handler)
        self.parser = RecursiveDescentParser(
            self.lexer.get_tokens(), self.error_handler
        )

    def _setup_parser(self, tokens: List[Token]):
        self.error_handler = create_autospec(ErrorHandler)
        self.parser = RecursiveDescentParser(tokens, self.error_handler)

    @pytest.mark.parametrize(
        "test_input", ["+10", "1=", "/", "(42 or 1", "34 and 21 or", "baka 42\n"]
    )
    def test_error_with_lexer(self, test_input):
        self._setup(test_input)
        self.parser.parse()
        assert self.error_handler.error.called

    @pytest.mark.skip(reason="This is not implemented yet.")
    def test_synchronization(self):
        pass

    def test_on_empty_input(self):
        self._setup("")
        self.parser.parse()
        assert not self.error_handler.error.called

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (
                "i \n",
                Stmts([ExprStmt(VarAccess(Token(None, 0, TokenType.IDENTIFIER)))]),
            ),
            (
                "7.2/3\n",
                Stmts(
                    [
                        ExprStmt(
                            BinaryExpr(
                                Literal(None),
                                Token(None, 0, TokenType.DIVIDE),
                                Literal(None),
                            )
                        )
                    ]
                ),
            ),
            (
                "(2+4) or 5\n",
                Stmts(
                    [
                        ExprStmt(
                            LogicalExpr(
                                GroupingExpr(
                                    BinaryExpr(
                                        Literal(None),
                                        Token(None, 0, TokenType.PLUS),
                                        Literal(None),
                                    )
                                ),
                                Token(None, 0, TokenType.OR),
                                Literal(None),
                            )
                        )
                    ]
                ),
            ),
            (
                "2*3 and 4\n",
                Stmts(
                    [
                        ExprStmt(
                            LogicalExpr(
                                BinaryExpr(
                                    Literal(None),
                                    Token(None, 0, TokenType.TIMES),
                                    Literal(None),
                                ),
                                Token(None, 0, TokenType.AND),
                                Literal(None),
                            )
                        )
                    ]
                ),
            ),
            (
                "3-2/1\n",
                Stmts(
                    [
                        ExprStmt(
                            BinaryExpr(
                                Literal(None),
                                Token(None, 0, TokenType.MINUS),
                                BinaryExpr(
                                    Literal(None),
                                    Token(None, 0, TokenType.DIVIDE),
                                    Literal(None),
                                ),
                            )
                        )
                    ]
                ),
            ),
        ],
    )
    def test_expression_stmt_with_lexer(self, test_input, expected):
        self._setup(test_input)
        nodes = self.parser.parse()
        assert not self.error_handler.error.called
        assert self.comparator.compare_nodes(nodes, expected)

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (
                "i <- 42 \n",
                Stmts(
                    [
                        AssStmt(
                            False, Token(None, 0, TokenType.IDENTIFIER), Literal(None)
                        )
                    ]
                ),
            ),
            (
                'fun <- have <- "one" \n',
                Stmts(
                    [
                        AssStmt(
                            False,
                            Token(None, 0, TokenType.IDENTIFIER),
                            Assign(
                                False,
                                Token(None, 0, TokenType.IDENTIFIER),
                                Literal(None),
                            ),
                        )
                    ]
                ),
            ),
            (
                "baka a <- 12\n",
                Stmts(
                    [
                        AssStmt(
                            True,
                            Token(None, 0, TokenType.IDENTIFIER),
                            Literal(None),
                        )
                    ]
                ),
            ),
        ],
    )
    def test_assignment_stmt(self, test_input, expected):
        self._setup(test_input)
        nodes = self.parser.parse()
        assert not self.error_handler.error.called
        assert self.comparator.compare_nodes(nodes, expected)

    def test_assignment_error(self):
        self._setup("temp <- 42 <- 3\n")
        self.parser.parse()
        assert self.error_handler.error.call_count == 1

        self._setup('var <- "one" <- "two" <- 3 \n')
        self.parser.parse()
        assert self.error_handler.error.call_count == 2

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (
                "nani i:\n  1\ndaijobu:\n 2\n",
                Stmts(
                    [
                        IfStmt(
                            VarAccess(Token(None, 0, TokenType.IDENTIFIER)),
                            BlockStmt([ExprStmt(Literal(None))]),
                            BlockStmt([ExprStmt(Literal(None))]),
                        )
                    ]
                ),
            ),
            (
                "nani i:\n  1\n  nani baito:\n   3\ndaijobu:\n 2\n",
                Stmts(
                    [
                        IfStmt(
                            VarAccess(Token(None, 0, TokenType.IDENTIFIER)),
                            BlockStmt(
                                [
                                    ExprStmt(Literal(None)),
                                    IfStmt(
                                        Literal(None),
                                        BlockStmt([ExprStmt(Literal(None))]),
                                        None,
                                    ),
                                ]
                            ),
                            BlockStmt([ExprStmt(Literal(None))]),
                        )
                    ]
                ),
            ),
        ],
    )
    def test_if_stmt(self, test_input, expected):
        self._setup(test_input)
        nodes = self.parser.parse()
        assert not self.error_handler.error.called
        assert self.comparator.compare_nodes(nodes, expected)

    def test_if_error(self):
        # Empty block not allowed
        self._setup("nani i:\n  #do nothing\n")
        self.parser.parse()
        assert self.error_handler.error.called

        # Else block intendation must match if block
        self._setup("nani i:\n daijobu g:\n  f\n")
        self.parser.parse()
        assert self.error_handler.error.called

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (
                "yandere true:\n do\n",
                Stmts(
                    [
                        WhileStmt(
                            Literal(None),
                            BlockStmt(
                                [
                                    ExprStmt(
                                        VarAccess(Token(None, 0, TokenType.IDENTIFIER))
                                    )
                                ]
                            ),
                        )
                    ]
                ),
            ),
        ],
    )
    def test_while_stmt(self, test_input, expected):
        self._setup(test_input)
        nodes = self.parser.parse()
        assert not self.error_handler.error.called
        assert self.comparator.compare_nodes(nodes, expected)

    def test_while_error(self):
        # Empty block not allowed
        self._setup("yandere i:\n  #do nothing\n")
        self.parser.parse()
        assert self.error_handler.error.called

    def test_continue_stmt(self):
        self._setup("kowai \n")
        self.parser.parse()
        assert self.error_handler.error.called

        self._setup("yandere 1:\n  kowai\n")
        self.parser.parse()
        assert not self.error_handler.error.called

    def test_break_stmt(self):
        self._setup("yamero \n")
        self.parser.parse()
        assert self.error_handler.error.called

        self._setup("yandere 1:\n  kowai\n")
        self.parser.parse()
        assert not self.error_handler.error.called
