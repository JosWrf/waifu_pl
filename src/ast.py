from abc import ABC
from src.Lexer import Token

class Expr(ABC):
    pass
    
class BinaryExpr(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right
          
class UnaryExpr(Expr):
    def __init__(self, operator: Token, right: Expr) -> None:
        self.operator = operator
        self.right = right
          
class GroupingExpr(Expr):
    def __init__(self, expression: Expr) -> None:
        self.expression = expression
          
class Literal(Expr):
    def __init__(self, value: Token) -> None:
        self.value = value
          
class Logical(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right
          
class Stmt(ABC):
    pass
     
