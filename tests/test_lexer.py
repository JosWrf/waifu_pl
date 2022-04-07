from src.Lexer import Lexer, TokenType
import pytest
from unittest.mock import create_autospec

from src.error_handler import ErrorHandler


class TestLexer:
    def _setLexer(self, text: str) -> None:
        self.error_handler = create_autospec(ErrorHandler)
        self.lexer = Lexer(text, self.error_handler)

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            ("<-", [TokenType.ASSIGNMENT, TokenType.EOF]),
            (".", [TokenType.DOT, TokenType.EOF]),
            ("<=", [TokenType.LESS_EQ, TokenType.EOF]),
            ("(", [TokenType.OP_PAR, TokenType.EOF]),
            ("1f", [TokenType.NUMBER, TokenType.IDENTIFIER, TokenType.EOF]),
            ("baka", [TokenType.NEWVAR, TokenType.EOF]),
            ("yamero", [TokenType.BREAK, TokenType.EOF]),
            ("kowai", [TokenType.CONTINUE, TokenType.EOF]),
            ("@", [TokenType.DECORATOR, TokenType.EOF]),
        ],
    )
    def test_simple_tokens(self, test_input, expected):
        self._setLexer(test_input)
        tokens = [token.type for token in self.lexer.get_tokens()]
        assert tokens == expected
        assert not self.error_handler.error.called

    @pytest.mark.parametrize("test_input", ["10.2334", "42"])
    def test_numbers(self, test_input):
        self._setLexer(test_input)
        assert not self.error_handler.error.called
        tokens = self.lexer.get_tokens()
        assert tokens[0].value == float(test_input)
        assert tokens[0].type == TokenType.NUMBER

    def test_empty_string(self):
        self._setLexer("")
        assert self.lexer.get_tokens()[0].type == TokenType.EOF
        assert not self.error_handler.error.called

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            (
                """yandere baito:\n  42\n""",
                [
                    TokenType.WHILE,
                    TokenType.NIL,
                    TokenType.COLON,
                    TokenType.NEWLINE,
                    TokenType.INDENT,
                    TokenType.NUMBER,
                    TokenType.NEWLINE,
                    TokenType.DEDENT,
                    TokenType.EOF,
                ],
            ),
            (
                """nani:\n  1\ndaijobu:\n  a\n""",
                [
                    TokenType.IF,
                    TokenType.COLON,
                    TokenType.NEWLINE,
                    TokenType.INDENT,
                    TokenType.NUMBER,
                    TokenType.NEWLINE,
                    TokenType.DEDENT,
                    TokenType.ELSE,
                    TokenType.COLON,
                    TokenType.NEWLINE,
                    TokenType.INDENT,
                    TokenType.IDENTIFIER,
                    TokenType.NEWLINE,
                    TokenType.DEDENT,
                    TokenType.EOF,
                ],
            ),
        ],
    )
    def test_block_declarations(self, test_input, expected):
        self._setLexer(test_input)
        tokens = [token.type for token in self.lexer.get_tokens()]
        assert tokens == expected
        assert not self.error_handler.error.called

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            (
                "desu:\n \n\n#cmt",
                [
                    TokenType.DEF,
                    TokenType.COLON,
                    TokenType.NEWLINE,
                    TokenType.EOF,
                ],
            ),
            (
                "s:\n\n f:\n  ",
                [
                    TokenType.IDENTIFIER,
                    TokenType.COLON,
                    TokenType.NEWLINE,
                    TokenType.INDENT,
                    TokenType.IDENTIFIER,
                    TokenType.COLON,
                    TokenType.NEWLINE,
                    TokenType.DEDENT,
                    TokenType.EOF,
                ],
            ),
        ],
    )
    def test_weird_block(self, test_input, expected):
        self._setLexer(test_input)
        tokens = [token.type for token in self.lexer.get_tokens()]
        assert tokens == expected
        assert not self.error_handler.error.called

    @pytest.mark.parametrize("test_input", ["&", "$", '"asd'])
    def test_wrong_tokens(self, test_input):
        self._setLexer(test_input)
        self.lexer.get_tokens()
        assert self.error_handler.error.called

    @pytest.mark.parametrize("test_input", ["f:\n g:\na", "l\n 42", "f:\na"])
    def test_wrong_block_intendation(self, test_input):
        self._setLexer(test_input)
        self.lexer.get_tokens()
        assert self.error_handler.error.called
