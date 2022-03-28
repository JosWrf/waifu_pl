from abc import ABC
from src.Lexer import Token
from typing import Any, List

class Expr(ABC):
    pass
    
class Assign(Expr):
    def __init__(self, new_var: bool, name: Token, expression: Expr) -> None:
        self.new_var = new_var
        self.name = name
        self.expression = expression
          
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
    def __init__(self, value: Any) -> None:
        self.value = value
          
class LogicalExpr(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr) -> None:
        self.left = left
        self.operator = operator
        self.right = right
          
class VarAccess(Expr):
    def __init__(self, name: Token) -> None:
        self.name = name
          
class Stmt(ABC):
    pass
     
class Stmts(Stmt):
    
    def __init__(self, stmts: List[Stmt]) -> None:
        self.stmts = stmts
          
    
class AssStmt(Stmt):
    
    def __init__(self, new_var: bool, name: Token, expression: Expr) -> None:
        self.new_var = new_var
        self.name = name
        self.expression = expression
          
    
class ExprStmt(Stmt):
    
    def __init__(self, expression: Expr) -> None:
        self.expression = expression
          
    
class BlockStmt(Stmt):
    
    def __init__(self, stmts: List[Stmt]) -> None:
        self.stmts = stmts
          
    
class IfStmt(Stmt):
    
    def __init__(self, cond: Expr, then: BlockStmt, other: BlockStmt) -> None:
        self.cond = cond
        self.then = then
        self.other = other
          
    
class WhileStmt(Stmt):
    
    def __init__(self, cond: Expr, body: BlockStmt) -> None:
        self.cond = cond
        self.body = body
          
    
class BreakStmt(Stmt):
    
        pass
    
class ContinueStmt(Stmt):
    
        pass
    
