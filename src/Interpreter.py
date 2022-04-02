import importlib
import inspect
from typing import Any, List
from src.Lexer import Token, TokenType
from src.ast import (
    AssStmt,
    Assign,
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
from src.environment import Environment
from src.error_handler import ErrorHandler
from src.errors import (
    BreakException,
    ContinueException,
    ReturnException,
    RuntimeException,
)
from src.stdlib.stdlib import CallableObj
from src.visitor import Visitor


class WaifuFunc(CallableObj):
    """This class corresponds to a runtime representation of user-defined
    functions. The function declaration node stores the body of the function and the
    formal parameters. All there's to call a function."""

    def __init__(self, node: FunctionDecl, closure: Environment) -> None:
        super().__init__()
        self.node = node
        self.closure = closure

    def call(self, interpreter: "Interpreter", args: List[Any]) -> Any:
        environment = Environment(interpreter.error_handler, self.closure)
        for param, arg in zip(self.node.params, args):
            environment.define(param.value, arg)
        try:
            interpreter._execute_block(self.node.body, environment)
        except ReturnException as re:
            return re.value

    def arity(self) -> int:
        return len(self.node.params)

    def __str__(self) -> str:
        """Python like output of function objects."""
        return f"<function {self.node.name.value}>"

    def __repr__(self) -> str:
        return self.__str__()


class Interpreter(Visitor):
    def __init__(self, error_handler: ErrorHandler) -> None:
        super().__init__()
        self.error_handler = error_handler
        self.environment = Environment(self.error_handler)
        self._load_stdlib("src.stdlib.stdlib")

    def _load_stdlib(self, mod_name: str):
        """Loads all classes defined in the stdlib module and packs instances in the
        global environment."""
        module = importlib.import_module(mod_name)
        for name, obj in inspect.getmembers(
            module,
            lambda member: inspect.isclass(member) and member.__module__ == mod_name,
        ):
            self.environment.define(name.lower(), obj())

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

    def _make_waifuish(self, value: Any) -> str:
        """Converts python representation of a waifu value to the waifu representation."""
        if value != 0 and not value:
            return "baito"
        if type(value) is float:
            if str(value).endswith(".0"):
                return str(value)[:-2]
        return str(value)

    def interpret(self, node: Any) -> Any:
        try:
            self.visit(node)
        except RuntimeException as re:
            self._report_runtime_err(re)

    def visit_functiondecl(self, node: FunctionDecl) -> None:
        """Similar to an assignment statement where we have an implicit variable
        declaration that is bound to a value of evaluating an expression.
        Inner functions are only declared when an outer function is called, thus
        we already have the closure setup by the function call."""
        self.environment.define(node.name.value, WaifuFunc(node, self.environment))

    def visit_stmts(self, node: Stmts) -> None:
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_breakstmt(self, node: BreakStmt) -> None:
        raise BreakException()

    def visit_continuestmt(self, node: ContinueStmt) -> None:
        raise ContinueException()

    def visit_returnstmt(self, node: ReturnStmt) -> None:
        raise ReturnException(node.err, self.visit(node.expr) if node.expr else None)

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
        self._execute_block(
            node.stmts, Environment(self.error_handler, self.environment)
        )

    def _execute_block(self, stmts: List[Stmts], environment: Environment) -> None:
        outer_scope = self.environment
        self.environment = environment
        try:  # this is required as return statements can throw an exception
            for stmt in stmts:
                self.visit(stmt)
        finally:
            self.environment = outer_scope

    def visit_assstmt(self, node: AssStmt) -> None:
        value = self.visit(node.expression)
        if node.new_var:
            self.environment.define(node.name.value, value)
        else:
            self.environment.assign(node.name, value)

    def visit_exprstmt(self, node: ExprStmt) -> None:
        self._make_waifuish(self.visit(node.expression))

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

    def visit_callexpr(self, node: CallExpr) -> Any:
        callee = self.visit(node.callee)
        args = [self.visit(expr) for expr in node.args]

        if not isinstance(callee, CallableObj):
            self._report_runtime_err(
                RuntimeException(node.calltoken, "Can only invoke callables.")
            )
        if not callee.arity() == len(args):
            self._report_runtime_err(
                RuntimeException(
                    node.calltoken,
                    f"Expected {len(callee.arity())} arguments but got{len(args)}",
                )
            )

        return callee.call(self, args)

    def visit_groupingexpr(self, node: GroupingExpr) -> Any:
        return self.visit(node.expression)

    def visit_literal(self, node: Literal) -> Any:
        return node.value

    def visit_varaccess(self, node: VarAccess) -> Any:
        return self.environment.get_value(node.name)
