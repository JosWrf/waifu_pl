from typing import Any, List, Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from src.Interpreter import Interpreter


@runtime_checkable
class CallableObj(Protocol):
    """Provides the interface that is to be implemented by foreign functions."""

    def call(self, interpreter: "Interpreter", args: List[Any]) -> Any:
        """Implements the function call and returns an object."""

    def arity(self) -> int:
        """Returns the number of formal paramters of the callable."""
