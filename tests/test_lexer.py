from src.Lexer import Lexer, TokenType
import pytest


class TestLexer:
    def _setLexer(self, text: str) -> None:
        self.lexer = Lexer(text)

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            ("<-", [TokenType.ASSIGNMENT, TokenType.EOF]),
            (".", [TokenType.DOT, TokenType.EOF]),
            ("<=", [TokenType.LESS_EQ, TokenType.EOF]),
            ("(", [TokenType.OP_PAR, TokenType.EOF]),
            ("baka", [TokenType.LET, TokenType.EOF]),
        ],
    )
    def test_simple_tokens(self, test_input, expected):
        self._setLexer(test_input)
        tokens = [token.type for token in self.lexer.get_tokens()]
        assert tokens == expected

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

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            (
                "desu:\n \n#cmt",
                [
                    TokenType.DEF,
                    TokenType.COLON,
                    TokenType.NEWLINE,
                    TokenType.INDENT,
                    TokenType.DEDENT,
                    TokenType.EOF,
                ],
            ),
            (
                "s:\n f:\n  ",
                [
                    TokenType.IDENTIFIER,
                    TokenType.COLON,
                    TokenType.NEWLINE,
                    TokenType.INDENT,
                    TokenType.IDENTIFIER,
                    TokenType.COLON,
                    TokenType.NEWLINE,
                    TokenType.INDENT,
                    TokenType.DEDENT,
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
