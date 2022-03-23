from typing import Any


class ErrorHandler:
    """Reports error messages and serves as the subject for the
    interpreter which is its observer."""

    def registerObserver(self, observer: Any) -> None:
        self.observer = observer

    def notifyObserver(self) -> None:
        self.observer.update()

    def error(self, message: str) -> None:
        print(message)
        self.notifyObserver()
