from typing import Any, Tuple


class Environment:
    def __init__(self, outer: "Environment" = None) -> None:
        self.outer = outer
        self.bindings = []

    def define(self, value: Any) -> None:
        self.bindings.append(value)

    def define_resolved(self, value: Any, indices: Tuple[int, int]) -> None:
        """This method bridges the gap of the dict used in the resolver and the
        list used in the interpreter environment. As long as no function/classes
        are redefined no issue arises. However, if one redclares a function of the
        same name, the node will get resolved to the old function which is still present
        in our list but which is overridden in the dictionary."""
        if indices:
            # global function/class is redefined
            self.bindings[indices[1]] = value
        else:
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
