from unittest.mock import create_autospec

from src.Lexer import Lexer
from src.Parser import RecursiveDescentParser
from src.Resolver import Resolver

from src.error_handler import ErrorHandler
from src.module import Module
from src.module_loader import ModuleLoader
from src.waifu_interpreter import WaifuInterpreter


class TestResolver:
    def _setup(self, text: str) -> None:
        self.error_handler = create_autospec(ErrorHandler)
        self.lexer = Lexer(text, self.error_handler)
        self.parser = RecursiveDescentParser(
            self.lexer.get_tokens(), self.error_handler
        )
        self.resolver = Resolver(
            self.error_handler,
            Module("", None, WaifuInterpreter(ModuleLoader(), self.error_handler)),
        )
        self.resolver.resolve(self.parser.parse())

    def test_return_error(self):
        self._setup("shinu 1\n")
        assert self.error_handler.error.called

    def test_resolved_vars(self):
        self._setup("i <- 10\ni\n")
        assert len(self.resolver.module.waifu_interpreter.resolved_vars) == 1

        assert (
            list(self.resolver.module.waifu_interpreter.resolved_vars.values())[0] == 0
        )
        assert not self.error_handler.error.called

        self._setup("desu f(a):\n  desu g(b):\n    a<-b\n  g(a)\n  shinu a\nf(12)\n")

        resolved_indices = [
            (key.name.value, index)
            for key, index in self.resolver.module.waifu_interpreter.resolved_vars.items()
        ]
        expected = [("b", 0), ("a", 1), ("g", 0), ("a", 0), ("a", 0), ("f", 0)]
        assert expected == resolved_indices
        assert not self.error_handler.error.called

    def test_baka_error(self):
        # Need last expression statement to use i
        self._setup("yandere baito:\n  i <- 3\n  baka i <- 4\n  i\n")
        assert self.error_handler.error.called

        # global baka is allowed
        self._setup("baka i <- 2\nbaka i <- 3\ni\n")
        assert not self.error_handler.error.called

    def test_unused_vars(self):
        self._setup("unused <- 4\nsame <- unused\n")
        assert self.error_handler.error.called

        self._setup("desu g(f):\n  f()\n@g\ndesu h():\n  print(baito)\n")
        assert not self.error_handler.error.called

    def test_function_redeclaration(self):
        self._setup("desu f():\n desu g():\n  g()\n desu g():\n  g()\n f()\n")
        assert self.error_handler.error.called

        # Global function redclarations are allowed
        self._setup("desu g():\n g()\ndesu g():\n g()\n")
        assert not self.error_handler.error.called

    def test_class_declaration(self):
        self._setup("waifu y:\n desu f():\n  watashi\n")

        assert not self.error_handler.error.called
        # Class y is defined in global scope
        assert self.resolver.globals["y"]
        # watashi is resolved to scope surrounding f()'s body
        this_ref = list(self.resolver.module.waifu_interpreter.resolved_vars.values())[
            0
        ]
        assert this_ref == 1

    def test_supercls_declaration(self):
        self._setup(
            "waifu x:\n desu g():\n  shinu\nwaifu y neesan x:\n desu f():\n  haha.g()\n"
        )

        assert not self.error_handler.error.called
        # Classes x,y is defined in global scope
        assert self.resolver.globals["x"]
        assert self.resolver.globals["y"]

        resolved = [
            (key.name.value, index)
            for key, index in self.resolver.module.waifu_interpreter.resolved_vars.items()
        ]
        # x is resolved to global scope
        # haha is resolved to scope surrounding this-scope and method body scope
        # G is stored in the same superref node as haha so both resolve to the same scope
        expected = [("x", 0), ("g", 2)]

        assert resolved == expected

    def test_this_error(self):
        # Watashi may only be called in classes
        self._setup("watashi\n")
        assert self.error_handler.error.called

    def test_super_error(self):
        self._setup("waifu c:\n desu h():\n  haha.f()\n")
        # Can only call haha in subclasses
        assert self.error_handler.error.called
