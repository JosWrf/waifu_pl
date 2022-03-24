import sys
from src.Interpreter import Interpreter
from src.Lexer import Lexer
from src.Parser import RecursiveDescentParser
from src.error_handler import ErrorHandler


def read_text(path: str) -> str:
    try:
        with open(path, "r") as f:
            buffer = f.read()
        return buffer
    except FileNotFoundError:
        print(f"File at path {path} does not exist.")
        sys.exit(-1)


class Waifu:
    def __init__(self, error_handler: ErrorHandler) -> None:
        self.err = False
        self.error_handler = error_handler
        self.error_handler.registerObserver(self)

    def interpret(self, path: str) -> None:
        text = read_text(path)
        self.lexer = Lexer(text, self.error_handler)

    def update(self) -> None:
        """Called from the error_handler subject error method."""
        self.err = True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: waifu [path]")
        sys.exit(-1)
    error_handler = ErrorHandler()
    waifu = Waifu(error_handler)
    waifu.interpret(sys.argv[1])
    tokens = waifu.lexer.get_tokens()
    if waifu.err:
        sys.exit(-1)
    parser = RecursiveDescentParser(tokens, error_handler)
    ast = parser.parse()
    if waifu.err:
        sys.exit(-1)
    interpreter = Interpreter()
    print(interpreter.interpret(ast))