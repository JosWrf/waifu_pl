from typing import Any
from src.Lexer import TokenType
from src.ast import Expr
from src.visitor import Visitor


class Interpreter(Visitor):
    # TODO: Add error handling and runtime error reporting
    def __init__(self) -> None:
        super().__init__()

    def interpret(self, node: Any) -> Any:
        return self.visit(node)

    def visit_binaryexpr(self, node: Expr) -> Any:
        # TODO: Add casts and conversions that interface between python and waifu
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.operator.type == TokenType.PLUS:
            return left + right
        if node.operator.type == TokenType.MINUS:
            return left - right
        if node.operator.type == TokenType.DIVIDE:
            return left / right
        if node.operator.type == TokenType.TIMES:
            return left * right
        if node.operator.type == TokenType.LESS:
            return left < right
        if node.operator.type == TokenType.LESS_EQ:
            return left <= right
        if node.operator.type == TokenType.GREATER:
            return left > right
        if node.operator.type == TokenType.GREATER_EQ:
            return left >= right
        if node.operator.type == TokenType.EQUAL:
            return left == right
        if node.operator.type == TokenType.UNEQUAL:
            return left != right

    def visit_logicalexpr(self, node: Expr) -> Any:
        # TODO: Add casts and conversions
        left = self.visit(node.left)
        if node.operator == TokenType.OR:
            if left:
                return left
        else:
            if not left:
                return left

        return self.visit(node.right)

    def visit_unaryexpr(self, node: Expr) -> Any:
        # TODO: Add casts and conversions
        operand = self.visit(node.right)
        if node.operator.type == TokenType.MINUS:
            return -operand
        if node.operator.type == TokenType.NOT:
            return not operand

    def visit_groupingexpr(self, node: Expr) -> Any:
        return self.visit(node.expression)

    def visit_literal(self, node: Any) -> Any:
        return node.value
