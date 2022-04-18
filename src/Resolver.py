import enum
import importlib
import inspect
from typing import Any, Dict, Tuple
from src.Lexer import Token
from src.ast import (
    Assign,
    AssStmt,
    BinaryExpr,
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
    ImportStmt,
    Literal,
    LogicalExpr,
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
from src.module import Module
from src.visitor import Visitor


class Context(enum.Enum):
    FUNCTION = enum.auto()
    METHOD = enum.auto()
    CONSTRUCTOR = enum.auto()
    OTHER = enum.auto()


class ClassContext(enum.Enum):
    CLASS = enum.auto()
    SUBCLASS = enum.auto()
    OTHER = enum.auto()


class Resolver(Visitor):
    """Performs a variable resolution pass. When not using baka in
    assignments we must check whether we define a variable or have to
    resolve."""

    def __init__(self, error_handler: ErrorHandler, module: Module) -> None:
        super().__init__()
        self.scopes = []
        self.unused_vars = []
        self.globals = {}
        self.resolved_vars = {}
        self.error_handler = error_handler
        self.function = Context.OTHER
        self.cls_context = ClassContext.OTHER
        self.module = module  # needed to preload the names of the imported module
        self._load_stdlib("src.stdlib.stdlib")

    def _load_stdlib(self, mod_name: str):
        """Loads the names of all standard functions in the global scope."""
        module = importlib.import_module(mod_name)
        for name, _ in inspect.getmembers(
            module,
            lambda member: inspect.isclass(member) and member.__module__ == mod_name,
        ):
            self.globals[name.lower()] = (True, None)

    def _semantic_error(self, err_token: Token, message: str):
        message = f"Line[{err_token.line}]: {message}"
        self.error_handler.error(message)

    def _check_defined(self, name: Token, message: str) -> None:
        """Called when baka is in front of assignment statements or assigns.
        Also called for local functions with names. Top-level functions
        may be redeclared."""
        for scope in self.scopes:
            if name.value in scope:
                self._semantic_error(name, message)
                return

    def _report_unused(self):
        if not self.unused_vars:
            return
        message = "Warning! the following variables are unused:\n"
        for unused in self.unused_vars:
            message += f"Line[{unused.line}]: {unused.value}\n"
        self.error_handler.error(message)

    def _check_unused(self, scope: Dict[str, Tuple[bool, Token]]) -> None:
        """Called everytime a block is popped of the scope stack."""
        self.unused_vars += [used[1] for used in scope.values() if not used[0]]

    def resolve(self, node: Stmts) -> Dict[Expr, int]:
        """Entry point for the next pipeline stage after generating the ast."""
        self.visit(node)
        self._check_unused(self.globals)
        self._report_unused()
        return self.resolved_vars

    def _define(self, name: Token, use: bool = False) -> None:
        """Use should only be set to True when defining functions and
        classes. Not using them is not a mistake, especially if modules
        are supported."""
        if self.scopes:
            self.scopes[-1][name.value] = (use, name)
        else:
            self.globals[name.value] = (use, name)

    def _resolve(self, name: Token, node: Any, use=False) -> bool:
        """Assigning to a variable does not do shit if it's not read at some point."""
        for index, scope_table in enumerate(reversed(self.scopes)):
            if name.value in scope_table.keys():
                if use:
                    scope_table[name.value] = (use, name)
                self.resolved_vars[node] = index
                return True
        # Needed so that no new variables are defined when resolving
        # would lead to a global variable.
        if name.value in self.globals.keys():
            if use:
                self.globals[name.value] = (use, name)
            self.resolved_vars[node] = len(self.scopes)
            return True
        return False

    def visit_assign(self, node: Assign) -> None:
        self.visit(node.expression)
        if node.new_var:
            message = f"Can't use 'baka' cause '{node.name.value}' is already defined in current scope."
            self._check_defined(node.name, message)
        if node.new_var or not self._resolve(node.name, node, True):
            self._define(node.name)
        else:
            pass

    def visit_setproperty(self, node: SetProperty) -> None:
        self.visit(node.obj)
        self.visit(node.value)

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

    def visit_objref(self, node: ObjRef) -> None:
        """Resolve this to current object. Not using True to
        count this as being used is fine, it saves calculating
        the hashfunction for the scope table."""
        if self.cls_context == ClassContext.OTHER:
            self._semantic_error(node.name, "Can only use 'watashi' in class context.")
            return
        self._resolve(node.name, node)

    def visit_superref(self, node: SuperRef) -> None:
        """Resolve super to the current superclass object."""
        if self.cls_context != ClassContext.SUBCLASS:
            self._semantic_error(
                node.super, "Can only use 'haha' inside methods of subclasses."
            )
        self._resolve(node.super, node)

    def visit_varaccess(self, node: VarAccess) -> None:
        self._resolve(node.name, node, True)

    def visit_callexpr(self, node: CallExpr) -> None:
        self.visit(node.callee)
        for arg in node.args:
            self.visit(arg)

    def visit_propertyaccess(self, node: PropertyAccess) -> None:
        """We can dynamically add fields to objects, thus we would need a runtime
        representation of objects in the static analyzer to statically resolve."""
        self.visit(node.obj)

    def visit_groupingexpr(self, node: GroupingExpr) -> None:
        self.visit(node.expression)

    def visit_stmts(self, node: Stmts) -> None:
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_importstmt(self, node: ImportStmt) -> None:
        """Imports should be statically resolved, such that the module's own variables can
        also be resolved in a correct way. If we were to resolve and then import, there'd be
        no way of statically resolving."""
        # TODO: Meditate on this - add names to current scope which must be the global scope
        # Just load the names of the exported variables in the global scope
        module = self.module.waifu_interpreter.import_module(node.name)
        import_stuff = module.exportable_vars
        for variable in import_stuff:
            self.globals[variable] = (False, node.keyword)

    def visit_classdecl(self, node: ClassDecl) -> None:
        current_cls = self.cls_context
        self.cls_context = ClassContext.CLASS
        # Classes are marked as used when defined
        self._define(node.name, True)

        if node.supercls:
            self.cls_context = ClassContext.SUBCLASS
            if node.name.value in [val.name.value for val in node.supercls]:
                self._semantic_error(
                    node.supercls.name, "Classes can't be their own superclass."
                )
            for supercls in node.supercls:
                self.visit(supercls)

            self.scopes.append({"haha": (True, None)})

        self.scopes.append({"watashi": (True, None)})
        # Method names are not defined -> not checked whether they're used in a program
        for method in node.methods:
            self._resolve_callable(
                method,
                Context.METHOD
                if method.name.value != "shison"
                else Context.CONSTRUCTOR,
            )
        self.scopes.pop()
        if node.supercls:
            self.scopes.pop()
        self.cls_context = current_cls

    def visit_functiondecl(self, node: FunctionDecl) -> None:
        # Decorating functions must also be resolved
        if node.decorator:
            self.visit(node.decorator)
        # Lambdas will not be bound
        if node.name.value != "":
            message = f"Can not redefine function as '{node.name.value}' already exists in current scope."
            self._check_defined(node.name, message)
            # Functions will be marked as used when defined
            self._define(node.name, True)

        self._resolve_callable(node, Context.FUNCTION)

    def _resolve_callable(self, node: Stmt, context: Context) -> None:
        """Auxilary method used to resolve functions/methods."""
        current_context = self.function
        self.function = context
        self.scopes.append({param.value: (False, param) for param in node.params})
        for stmt in node.body:
            self.visit(stmt)
        self.function = current_context
        self._check_unused(self.scopes.pop())

    def visit_blockstmt(self, node: BlockStmt) -> None:
        self.scopes.append({})
        for stmt in node.stmts:
            self.visit(stmt)
        self._check_unused(self.scopes.pop())

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
        if self.function == Context.OTHER:
            self._semantic_error(node.err, "Can't use 'shinu' outside of functions.")
            return
        if self.function == Context.CONSTRUCTOR:
            self._semantic_error(node.err, "Can't use 'shinu' in constructors.")
        if node.expr:
            self.visit(node.expr)
