import enum
import importlib
import inspect
from typing import Any, Dict
from src.Lexer import Token
from src.ast import (
    Assign,
    AssStmt,
    BinaryExpr,
    BlockStmt,
    BreakStmt,
    CallExpr,
    ContinueStmt,
    Expr,
    ExprStmt,
    FunctionDecl,
    GroupingExpr,
    IfStmt,
    Literal,
    LogicalExpr,
    ReturnStmt,
    Stmts,
    UnaryExpr,
    VarAccess,
    WhileStmt,
)
from src.error_handler import ErrorHandler
from src.visitor import Visitor


class Context(enum.Enum):
    FUNCTION = enum.auto()
    OTHER = enum.auto()


class Resolver(Visitor):
    """Performs a variable resolution pass. When not using baka in
    assignments we must check whether we define a variable or have to
    resolve."""

    def __init__(self, error_handler: ErrorHandler) -> None:
        super().__init__()
        self.scopes = []
        self.globals = []
        self.resolved_vars = {}
        self.error_handler = error_handler
        self.function = None
        self._load_stdlib("src.stdlib.stdlib")

    def _load_stdlib(self, mod_name: str):
        """Loads the names of all standard functions in the global scope."""
        module = importlib.import_module(mod_name)
        for name, _ in inspect.getmembers(
            module,
            lambda member: inspect.isclass(member) and member.__module__ == mod_name,
        ):
            self.globals.append(name.lower())

    def _semantic_error(self, err_token: Token, message: str):
        message = f"Line[{err_token.line}]: {message}"
        self.error_handler.error(message)

    def _check_defined(self, name: Token, message: str) -> None:
        """Called when baka is in front of assignment statements or assigns.
        Also called when local functions with names."""
        for scope in self.scopes:
            if name.value in scope:
                self._semantic_error(name, message)
                return

    def resolve(self, node: Stmts) -> Dict[Expr, int]:
        self.visit(node)
        return self.resolved_vars

    def _define(self, name: Token) -> None:
        if self.scopes:
            self.scopes[-1].append(name.value)
        else:
            self.globals.append(name.value)

    def _resolve(self, name: Token, node: Any) -> bool:
        for index, scope_table in enumerate(reversed(self.scopes)):
            if name.value in scope_table:
                self.resolved_vars[node] = index
                return True
        # Needed so that no new variables are defined when resolving
        # would lead to a global variable.
        if name.value in self.globals:
            self.resolved_vars[node] = len(self.scopes)
            return True
        return False

    def visit_assign(self, node: Assign) -> None:
        self.visit(node.expression)
        if node.new_var:
            message = f"Can't use 'baka' cause '{node.name.value}' is already defined in current scope."
            self._check_defined(node.name, message)
        if node.new_var or not self._resolve(node.name, node):
            self._define(node.name)
        else:
            pass

    def visit_binaryexpr(self, node: BinaryExpr) -> None:
        self.visit(node.left)
        self.visit(node.right)

    def visit_unaryexpr(self, node: UnaryExpr) -> None:
        self.visit(node.right)

    def visit_logicalexpr(self, node: LogicalExpr) -> None:
        self.visit(node.left)
        self.visit(node.right)

    def visit_literal(self, node: Literal) -> None:
        return None

    def visit_varaccess(self, node: VarAccess) -> None:
        self._resolve(node.name, node)

    def visit_callexpr(self, node: CallExpr) -> None:
        self.visit(node.callee)
        for arg in node.args:
            self.visit(arg)

    def visit_groupingexpr(self, node: GroupingExpr) -> None:
        self.visit(node.expression)

    def visit_stmts(self, node: Stmts) -> None:
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_functiondecl(self, node: FunctionDecl) -> None:
        # Decorating functions must also be resolved
        if node.decorator:
            self._resolve(node.decorator, node)
        # Lambdas will not be bound
        if node.name.value != "":
            message = f"Can not redefine function as '{node.name.value}' already exists in current scope."
            self._check_defined(node.name, message)
            self._define(node.name)

        current_context = self.function
        self.function = Context.FUNCTION
        self.scopes.append([param.value for param in node.params])
        for stmt in node.body:
            self.visit(stmt)
        self.function = current_context
        self.scopes.pop()

    def visit_blockstmt(self, node: BlockStmt) -> None:
        self.scopes.append([])
        for stmt in node.stmts:
            self.visit(stmt)
        self.scopes.pop()

    def visit_ifstmt(self, node: IfStmt) -> None:
        self.visit(node.cond)
        self.visit(node.then)
        if node.other:
            self.visit(node.other)

    def visit_whilestmt(self, node: WhileStmt) -> None:
        self.visit(node.cond)
        self.visit(node.body)

    def visit_assstmt(self, node: AssStmt) -> None:
        # Run initializer then put the variable in scope
        self.visit(node.expression)
        if node.new_var:
            message = f"Can't use 'baka' cause '{node.name.value}' is already defined in current scope."
            self._check_defined(node.name, message)
        if node.new_var or not self._resolve(node.name, node):
            self._define(node.name)
        else:
            pass

    def visit_exprstmt(self, node: ExprStmt) -> None:
        self.visit(node.expression)

    def visit_continuestmt(self, node: ContinueStmt) -> None:
        return None

    def visit_breakstmt(self, node: BreakStmt) -> None:
        return None

    def visit_returnstmt(self, node: ReturnStmt) -> None:
        if self.function != Context.FUNCTION:
            message = f"Can't use 'shinu' outside of functions."
            self._semantic_error(node.err, message)
        if node.expr:
            self.visit(node.expr)
