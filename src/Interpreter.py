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
    Stmts,
    SuperRef,
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
from src.module import Module
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

    def bind(self, obj: "WaifuObject"):
        this_env = Environment(self.closure)
        this_env.define("watashi", obj)
        return WaifuFunc(self.node, this_env)

    def call(self, interpreter: "Interpreter", args: List[Any]) -> Any:
        environment = Environment(self.closure)
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
        return (
            f"<function {self.node.name.value}>" if self.node.name.value else "<lambda>"
        )

    def __repr__(self) -> str:
        return self.__str__()


class WaifuObject:
    """Runtime representation of objects in the waifu language."""

    def __init__(self, cls: "WaifuClass") -> None:
        self.cls = cls
        self.fields = {}

    def get(self, name: Token) -> Any:
        if name.value in self.fields:
            return self.fields[name.value]

        method = self.cls.get_method(name)
        if method:
            return method

        raise RuntimeException(
            name, f"Property '{name.value}' does not exist for {self.__str__()}."
        )

    def set(self, name: Token, value: Any) -> None:
        self.fields[name.value] = value

    def __str__(self) -> str:
        return f"<object of {self.cls.__str__()}>"


class WaifuClass(WaifuObject, CallableObj):
    """Runtime representation of classes in the waifu language."""

    def __init__(
        self, name: str, super_cls: List["WaifuClass"], meta_cls: "WaifuClass"
    ) -> None:
        super(WaifuClass, self).__init__(meta_cls)
        self.name = name
        self.super_cls = super_cls
        self.methods = {}

    def call(self, interpreter: "Interpreter", args: List[Any]) -> Any:
        obj = WaifuObject(self)
        constructr = self.methods.get("shison")
        if constructr:
            constructr.bind(obj).call(interpreter, args)
        return obj

    def arity(self) -> int:
        constructr = self.methods.get("shison")
        if constructr:
            return constructr.arity()
        return 0

    def add_method(self, name: Token, method: WaifuFunc) -> None:
        self.methods[name.value] = method

    def get_method(self, name: Token) -> WaifuFunc:
        if name.value in self.methods:
            return self.methods[name.value]

        if self.super_cls:
            for super_cls in self.super_cls:
                method = super_cls.get_method(name)
                if method:
                    return method

    def __str__(self) -> str:
        return f"<class {self.name}>"


class Interpreter(Visitor):
    def __init__(
        self,
        error_handler: ErrorHandler,
        module: Module,
    ) -> None:
        super().__init__()
        self.error_handler = error_handler
        self.module = module
        self.environment = (
            module.scope
        )  # top-level scope of each module is aliased in the interpreter
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
            self._export()
        except RuntimeException as re:
            self._report_runtime_err(re)

    def _export(self) -> None:
        """Moves all identifiers of the imported module to the importing module."""
        for var in self.environment.bindings:
            self.module.exportable_vars.add(var)

    def visit_importstmt(self, node: ImportStmt) -> None:
        module = self.module.waifu_interpreter.import_module(node.name)
        import_stuff = module.exportable_vars
        for variable in import_stuff:
            self.module.import_name(variable, module)

    def visit_classdecl(self, node: ClassDecl) -> None:
        supercls = None
        if node.supercls:
            supercls = []
            for cls in node.supercls:
                sup_cls = self.visit(cls)
                supercls.append(sup_cls)
                if type(sup_cls) != WaifuClass:
                    self._report_runtime_err(
                        RuntimeException(
                            node.supercls.name, "Can only inherit from classes"
                        )
                    )

        # Like in SMALLTALK classes and metaclasses are conjoined twins
        # Add the metaclass of the superclass as superclass of the metaclass to allow
        # inheritance of class methods.
        meta_cls = WaifuClass(
            f"__{node.name.value}__",
            [sup.cls for sup in supercls] if supercls else None,
            None,
        )
        cls = WaifuClass(node.name.value, supercls, meta_cls)
        self.environment.define(node.name.value, cls)

        environment = self.environment
        if node.supercls:
            environment = Environment(environment)
            # Bind list of super classes in the methods enclosing environment
            environment.define("haha", supercls)

        for method in node.methods:
            (meta_cls if method.static else cls).add_method(
                method.name, WaifuFunc(method, environment)
            )

    def visit_functiondecl(self, node: FunctionDecl) -> Any:
        """Similar to an assignment statement where we have an implicit variable
        declaration that is bound to a value of evaluating an expression.
        Inner functions are only declared when an outer function is called, thus
        we already have the closure setup by the function call."""

        # Lambdas are expressions and need to return a function
        func = WaifuFunc(node, self.environment)
        if node.name.value == "":
            return func

        if node.decorator:
            self._decorated_function(node)
        else:
            self.environment.define(node.name.value, func)

    def _decorated_function(self, node: FunctionDecl) -> None:
        index = self.module.waifu_interpreter.resolved_vars.get(node.decorator)
        if index is None:
            self._report_runtime_err(
                RuntimeException(
                    node.decorator.name,
                    f"Decorating function '{node.decorator.name.value}' does not exist.",
                )
            )
        dec_func = self.environment.get_at_index(index, node.decorator.name.value)
        if not type(dec_func) is WaifuFunc:
            self._report_runtime_err(
                RuntimeException(node.name, "Can only use a function as a decorator.")
            )
        if dec_func.arity() != 1:
            self._report_runtime_err(
                RuntimeException(
                    node.name, "Can only pass one function argumnent to a decorator."
                )
            )

        # Wrapper function stores function object in its closure
        wrapper = dec_func.call(self, [WaifuFunc(node, self.environment)])

        self.environment.define(node.name.value, wrapper)

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
        self._execute_block(node.stmts, Environment(self.environment))

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
            index = self.module.waifu_interpreter.resolved_vars.get(node)
            if not index is None:
                self.environment.assign_at(value, index, node.name.value)
            else:
                self.environment.define(node.name.value, value)

    def visit_exprstmt(self, node: ExprStmt) -> None:
        self.visit(node.expression)

    def visit_setproperty(self, node: SetProperty) -> Any:
        obj = self.visit(node.obj)
        if not type(obj) is WaifuObject:
            self._report_runtime_err(
                RuntimeException(node.name, "Can only set properties on objects.")
            )
        value = self.visit(node.value)
        obj.set(node.name, value)
        return value

    def visit_assign(self, node: Assign) -> Any:
        value = self.visit(node.expression)
        if node.new_var:
            self.environment.define(node.name.value, value)
        else:
            index = self.module.waifu_interpreter.resolved_vars.get(node)
            if not index is None:
                self.environment.assign_at(value, index, node.name.value)
            else:
                self.environment.define(node.name.value, value)
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
                    f"Expected {callee.arity()} arguments but got{len(args)}",
                )
            )

        return callee.call(self, args)

    def visit_propertyaccess(self, node: PropertyAccess) -> Any:
        obj = self.visit(node.obj)

        if not isinstance(obj, WaifuObject):
            self._report_runtime_err(
                RuntimeException(
                    node.name, "Can only access properties on objects or classes."
                )
            )

        property = obj.get(node.name)
        if type(property) is WaifuFunc:
            return property.bind(obj)

        return property

    def visit_groupingexpr(self, node: GroupingExpr) -> Any:
        return self.visit(node.expression)

    def visit_literal(self, node: Literal) -> Any:
        return node.value

    def visit_objref(self, node: ObjRef) -> WaifuObject:
        index = self.module.waifu_interpreter.resolved_vars.get(node)
        return self.environment.get_at_index(index, "watashi")

    def visit_superref(self, node: SuperRef) -> WaifuFunc:
        """Acts like a mixture of a getter and this reference."""
        # Obtain the list of super class instances
        index = self.module.waifu_interpreter.resolved_vars.get(node)
        super_clsses = self.environment.get_at_index(index, "haha")

        # Get this from the object where the method referencing super was called;
        # it's right between super and the scope of the method body
        this = self.environment.get_at_index(index - 1, "watashi")

        for super_cls in super_clsses:
            method = super_cls.get_method(node.name)
            if method:
                break

        if not method:
            self._report_runtime_err(
                RuntimeException(
                    node.super,
                    f"No method {node.name.value} found in list of superclasses.",
                )
            )
        return method.bind(this)

    def visit_varaccess(self, node: VarAccess) -> Any:
        index = self.module.waifu_interpreter.resolved_vars.get(node)
        if not index is None:
            return self.environment.get_at_index(index, node.name.value)
        # Undefined variable case
        self._report_runtime_err(
            RuntimeException(node.name, f"Undefined variable '{node.name.value}'.")
        )
