from unittest.mock import create_autospec

import pytest
from src.Lexer import Lexer
from src.Parser import RecursiveDescentParser
from src.Resolver import Resolver

from src.error_handler import ErrorHandler


class TestResolver:
    def _setup(self, text: str) -> None:
        self.error_handler = create_autospec(ErrorHandler)
        self.lexer = Lexer(text, self.error_handler)
        self.parser = RecursiveDescentParser(
            self.lexer.get_tokens(), self.error_handler
        )
        self.resolver = Resolver(self.error_handler)
        self.resolved_vars = self.resolver.resolve(self.parser.parse())

    def test_return_error(self):
        self._setup("shinu 1\n")
        assert self.error_handler.error.called

    def test_resolved_vars(self):
        self._setup("i <- 10\ni\n")
        assert len(self.resolved_vars) == 1
        # I should be in the global scope thus (0,*)
        # Accessing the column index is kinda tough becasue we load the stdlib
        assert list(*self.resolved_vars.values())[0] == 0
        assert not self.error_handler.error.called

        self._setup("desu f(a):\n  desu g(b):\n    a<-b\n  g(a)\n  shinu a\nf(12)\n")
        assert len(self.resolved_vars) == 6
        # Remove call to f since it's in globals we only know its (0,*)
        resolved_indices = [
            indices
            for key, indices in self.resolved_vars.items()
            if key.name.value not in self.resolver.globals
        ]
        # First b is resolved which is the first element in the scope of g()'s body
        expected = [(0, 0), (1, 0), (0, 1), (0, 0), (0, 0)]
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

        self._setup("desu g(f):\n  f()\n@g\ndesu h():\n  print(baito)\nh()\n")
        assert not self.error_handler.error.called

    def test_function_redeclaration(self):
        self._setup("desu f():\n desu g():\n  g()\n desu g():\n  g()\n f()\n")
        assert self.error_handler.error.called

        # Global function redclarations are allowed
        self._setup("desu g():\n g()\ndesu g():\n g()\n")
        assert not self.error_handler.error.called
