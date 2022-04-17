import sys
from src.Interpreter import Interpreter
from src.Lexer import Lexer
from src.Parser import RecursiveDescentParser
from src.Resolver import Resolver
from src.error_handler import ErrorHandler
from src.module import Module, SourceFile
from src.module_loader import ModuleLoader
from pathlib import Path


class WaifuInterpreter:
    def __init__(self, loader: ModuleLoader, error_handler: ErrorHandler) -> None:
        self.loader = loader
        self.err = False
        self.error_handler = error_handler
        self.error_handler.registerObserver(self)
        self.loaded_modules = {}  # Dictionary of all loaded modules
        self.module_stack = []  # Top level module is currently executed

    def update(self) -> None:
        """Called from the error_handler subject error method."""
        runtime_err = self.error_handler.runtime_err
        if not runtime_err:
            self.err = True
        else:
            sys.exit(-1)

    def run(self, source_file: SourceFile) -> None:
        """Entry point for the main program to kick off interpretation
        after the first module was succesfully loaded."""
        module = Module(Path(source_file.path).stem, source_file, self)
        self.loaded_modules[module.name] = module
        self.evaluate_module(module)

    def evaluate_module(self, module: Module) -> None:
        """Called when a new module was loaded. It starts off interpreting
        the source text of the module."""
        self.module_stack.append(module)

        # Could copy common stuff for each module into the scope of the module
        self._interpret_module(module)

        self.module_stack.pop()
        module.sourcefile.text = (
            None  # free text buffer after interpreting file contents
        )

    def _interpret_module(self, module: Module) -> None:
        """Starts the entire compiler pipeline from the lexer all the way to the
        interpreter (tree walk interpreter) for the given module. If the evaluating
        the current module's text fails, then we just stop the entire process."""
        lexer = Lexer(module.sourcefile.text, self.error_handler)
        tokens = lexer.get_tokens()
        if self.err:
            sys.exit(-1)
        parser = RecursiveDescentParser(tokens, self.error_handler)
        ast = parser.parse()
        if self.err:
            sys.exit(-1)
        resolver = Resolver(self.error_handler)
        resolved_vars = resolver.resolve(ast)
        if self.err:
            sys.exit(-1)
        interpreter = Interpreter(self.error_handler, resolved_vars, module)
        interpreter.interpret(ast)
