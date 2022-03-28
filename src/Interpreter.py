from typing import Any
from src.Lexer import Token, TokenType
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
    Stmts,
    UnaryExpr,
    VarAccess,
    WhileStmt,
)
from src.environment import Environment
from src.error_handler import ErrorHandler
from src.errors import BreakException, ContinueException, RuntimeException
from src.visitor import Visitor


class Interpreter(Visitor):
    def __init__(self, error_handler: ErrorHandler) -> None:
        super().__init__()
        self.error_handler = error_handler
        self.environment = Environment(self.error_handler)

    def _boolean_eval(self, operand: Any) -> bool:
        """Implements evaluation of boolean expressions similar to lua."""
        if operand == False or operand == None:
            return False
        return True

    def _equality_eval(self, obj1: Any, obj2: Any) -> bool:
        """Implements equality based on pythons equality implementation."""
        return obj1 == obj2

    def _check_num_unary(self, operator: Token, operand: Any) -> None:
        if type(operand) is float:
            return
        raise RuntimeException(
            operator, f"Can only apply {operator} to numeric operand."
        )

    def _check_num_binary(self, operator: Token, left: Any, right: Any) -> None:
        if type(left) is float and type(right) is float:
            return
        raise RuntimeException(
            operator, f"Can only apply {operator} to numeric operands."
        )

    def _check_zero_dividend(self, operator: Token, right: Expr) -> None:
        if float(right) == 0:
            raise RuntimeException(operator, f"Can not divide by zero.")

    def _report_runtime_err(self, exception: RuntimeException) -> None:
        message = f"Line[{exception.token.line}]: {exception.message}"
        self.error_handler.error(message, True)

    def interpret(self, node: Any) -> Any:
        try:
            self.visit(node)
        except RuntimeException as re:
            self._report_runtime_err(re)

    def visit_stmts(self, node: Stmts) -> None:
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_breakstmt(self, node: BreakStmt) -> None:
        raise BreakException()

    def visit_continuestmt(self, node: ContinueStmt) -> None:
        raise ContinueException()

    def visit_whilestmt(self, node: WhileStmt) -> None:
        try:
            while self._boolean_eval(self.visit(node.cond)):
                try:
                    self.visit(node.body)
                except ContinueException:
                    pass
        except BreakException:
            pass

    def visit_ifstmt(self, node: IfStmt) -> None:
        if self._boolean_eval(self.visit(node.cond)):
            self.visit(node.then)
        elif node.other:
            self.visit(node.other)

    def visit_blockstmt(self, node: BlockStmt) -> None:
        outer_scope = self.environment
        inner_scope = Environment(self.error_handler, outer_scope)
        self.environment = inner_scope
        for stmt in node.stmts:
            self.visit(stmt)

        self.environment = outer_scope

    def visit_assstmt(self, node: AssStmt) -> None:
        value = self.visit(node.expression)
        if node.new_var:
            self.environment.define(node.name, value)
        else:
            self.environment.assign(node.name, value)

    def visit_exprstmt(self, node: ExprStmt) -> None:
        # TODO: replace later on when print() is a library function
        print(self._make_waifuish(self.visit(node.expression)))

    def visit_assign(self, node: Assign) -> None:
        value = self.visit(node.expression)
        if node.new_var:
            self.environment.define(node.name, value)
        else:
            self.environment.assign(node.name, value)
        return value

    def visit_binaryexpr(self, node: BinaryExpr) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.operator.type == TokenType.PLUS:
            if type(left) == str or type(left) == str:
                return self._make_waifuish(left) + self._make_waifuish(right)
            else:
                self._check_num_binary(node.operator, left, right)
                return float(left) + float(right)
        if node.operator.type == TokenType.MINUS:
            self._check_num_binary(node.operator, left, right)
            return float(left) - float(right)
        if node.operator.type == TokenType.DIVIDE:
            self._check_num_binary(node.operator, left, right)
            self._check_zero_dividend(node.operator, right)
            return float(left) / float(right)
        if node.operator.type == TokenType.TIMES:
            self._check_num_binary(node.operator, left, right)
            return (left) * (right)
        if node.operator.type == TokenType.LESS:
            self._check_num_binary(node.operator, left, right)
            return float(left) < float(right)
        if node.operator.type == TokenType.LESS_EQ:
            self._check_num_binary(node.operator, left, right)
            return float(left) <= float(right)
        if node.operator.type == TokenType.GREATER:
            self._check_num_binary(node.operator, left, right)
            return float(left) > float(right)
        if node.operator.type == TokenType.GREATER_EQ:
            self._check_num_binary(node.operator, left, right)
            return float(left) >= float(right)
        if node.operator.type == TokenType.EQUAL:
            return self._equality_eval(left, right)
        if node.operator.type == TokenType.UNEQUAL:
            return not self._equality_eval(left, right)

    def visit_logicalexpr(self, node: LogicalExpr) -> Any:
        left = self.visit(node.left)
        if node.operator == TokenType.OR:
            if self._boolean_eval(left):
                return left
        else:
            if not self._boolean_eval(left):
                return left

        return self.visit(node.right)

    def visit_unaryexpr(self, node: UnaryExpr) -> Any:
        operand = self.visit(node.right)
        if node.operator.type == TokenType.MINUS:
            self._check_num_unary(node.operator, operand)
            return -float(operand)
        if node.operator.type == TokenType.NOT:
            return not self._boolean_eval(operand)

    def visit_groupingexpr(self, node: GroupingExpr) -> Any:
        return self.visit(node.expression)

    def visit_literal(self, node: Literal) -> Any:
        return node.value

    def visit_varaccess(self, node: VarAccess) -> Any:
        return self.environment.get_value(node.name)

    def _make_waifuish(self, value: Any) -> str:
        """Converts python representation of a waifu value to the waifu representation."""
        if not value:
            return "baito"
        if type(value) is float:
            if str(value).endswith(".0"):
                return str(value)[:-2]
        return str(value)
