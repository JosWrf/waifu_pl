import sys
from typing import Any


class ErrorHandler:
    """Reports error messages and serves as the subject for the
    interpreter which is its observer."""

    def __init__(self) -> None:
        self._runtime_err = False

    @property
    def runtime_err(self) -> bool:
        return self._runtime_err

    def registerObserver(self, observer: Any) -> None:
        self.observer = observer

    def notifyObserver(self) -> None:
        self.observer.update()

    def error(self, message: str, runtime_err: bool = False) -> None:
        module_path = self.observer.get_current_module_path()
        message = "In module " + module_path + " " + message
        self._runtime_err = runtime_err
        print(message, file=sys.stderr)
        self.notifyObserver()
