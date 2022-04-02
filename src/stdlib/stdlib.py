from typing import TYPE_CHECKING, Any, List
from src.stdlib.lib_interface import CallableObj

if TYPE_CHECKING:
    from src.Interpreter import Interpreter

"""This is the place where all foreign functions are implemented."""


class Print(CallableObj):
    def call(self, interpreter: "Interpreter", args: List[Any]) -> Any:
        print(interpreter._make_waifuish(args[0]))

        return None

    def arity(self) -> int:
        return 1


class Input(CallableObj):
    def call(self, interpreter: "Interpreter", args: List[Any]) -> Any:
        return interpreter._make_waifuish(input(interpreter._make_waifuish(args[0])))

    def arity(self) -> int:
        return 1
