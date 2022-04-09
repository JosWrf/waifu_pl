from typing import Any


class Environment:
    def __init__(self, outer: "Environment" = None) -> None:
        self.outer = outer
        self.bindings = []

    def define(self, value: Any) -> None:
        self.bindings.append(value)

    def assign_at(self, value: Any, scope: int, index: int) -> None:
        if scope == 0:
            self.bindings[index] = value
            return

        self.outer.assign_at(value, scope - 1, index)

    def get_at_index(self, scope: int, index: int) -> Any:
        if scope == 0:
            return self.bindings[index]

        return self.outer.get_at_index(scope - 1, index)
