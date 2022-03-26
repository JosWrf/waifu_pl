from typing import Any
from src.Lexer import Token, TokenType
from src.ast import (
    BinaryExpr,
    Expr,
    ExprStmt,
    GroupingExpr,
    Literal,
    LogicalExpr,
    Stmts,
    UnaryExpr,
    VarAccess,
    VarDecl,
)
from src.environment import Environment
from src.error_handler import ErrorHandler
from src.visitor import Visitor


class RuntimeException(RuntimeError):
    def __init__(self, token: Token, message: str) -> None:
        super().__init__()
        self.token = token
        self.message = message


class Interpreter(Visitor):
    def __init__(self, error_handler: ErrorHandler, environment: Environment) -> None:
        super().__init__()
        self.error_handler = error_handler
        self.environment = environment

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

    def visit_vardecl(self, node: VarDecl) -> None:
        if node.initializer:
            value = self.visit(node.initializer)
            self.environment.set_value(node.name, value)

    def visit_exprstmt(self, node: ExprStmt) -> None:
        # TODO: replace later on when print() is a library function
        print(self._make_waifuish(self.visit(node.expression)))

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
        # TODO: Add casts and conversions
        left = self.visit(node.left)
        if node.operator == TokenType.OR:
            if left:
                return left
        else:
            if not left:
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
