import enum
from enum import Enum
from typing import Any, List


class TokenType(Enum):
    PLUS = enum.auto()
    MINUS = enum.auto()
    TIMES = enum.auto()
    DIVIDE = enum.auto()
    OP_PAR = enum.auto()
    CL_PAR = enum.auto()
    COLON = enum.auto()
    DOT = enum.auto()
    NEWLINE = enum.auto()
    INDENT = enum.auto()
    DEDENT = enum.auto()

    # Literal
    NUMBER = enum.auto()
    IDENTIFIER = enum.auto()
    STRING = enum.auto()

    # Relational ops and ass
    EQUAL = enum.auto()
    UNEQUAL = enum.auto()
    GREATER = enum.auto()
    GREATER_EQ = enum.auto()
    LESS = enum.auto()
    LESS_EQ = enum.auto()
    ASSIGNMENT = enum.auto()

    # Keywords
    OR = enum.auto()
    AND = enum.auto()
    NOT = enum.auto()
    IF = enum.auto()
    ELSE = enum.auto()
    NIL = enum.auto()
    RETURN = enum.auto()
    TRUE = enum.auto()
    FALSE = enum.auto()
    DEF = enum.auto()
    LET = enum.auto()
    WHILE = enum.auto()

    EOF = enum.auto()


class Token:
    """Stores attributes of the lexical analysis, which
    is either a lexeme or a value."""

    def __init__(self, value: Any, line: int, type: TokenType) -> None:
        self.value = value
        self.line = line
        self.type = type

    def __str__(self) -> str:
        return f"Token({self.type}, {self.line}, {self.value})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, object: Any) -> bool:
        return (
            isinstance(object, Token)
            and self.value == object.value
            and self.type == object.type
        )


class Lexer:
    """A simple Lexer that reads through a file and groups the
    words into tokens.
    """

    keywords = {
        "and": TokenType.AND,
        "or": TokenType.OR,
        "not": TokenType.NOT,
        "nani": TokenType.IF,
        "daijobu": TokenType.ELSE,
        "baka": TokenType.LET,
        "true": TokenType.TRUE,
        "false": TokenType.FALSE,
        "baito": TokenType.NIL,
        "desu": TokenType.DEF,
        "shinu": TokenType.RETURN,
        "yandere": TokenType.WHILE,
    }

    simple_tokens = {
        "(": TokenType.OP_PAR,
        ")": TokenType.CL_PAR,
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.TIMES,
        "/": TokenType.DIVIDE,
        ".": TokenType.DOT,
        "=": TokenType.EQUAL,
    }

    def __init__(self, text: str) -> None:
        self.start_pos = 0  # the position of the buffer before testing any automaton
        self.curr_pos = (
            0  # the position of the buffer after starting to test an automaton
        )
        self.line = 1
        self.last_newline = 0
        self.text = text
        self.tokens = []
        self.indent_pos = 0
        self.indent_stack = []
        self.empty_line = True

    def is_eof(self) -> bool:
        return self.curr_pos >= len(self.text)

    def get_tokens(self) -> List[Token]:
        while not self.is_eof():
            self.start_pos = self.curr_pos
            self._get_token()
        self._close_last_block()
        self._add_token(TokenType.EOF)
        return self.tokens

    def _close_last_block(self) -> None:
        """This dedents the last block in the file. So the position of the
        cursor after the last newline does not matter."""
        while self.indent_stack:
            self._add_token(TokenType.DEDENT, self.indent_pos)
            self.indent_pos = self.indent_stack.pop()

    def _add_token(self, type: TokenType, value: Any = None) -> None:
        self.tokens.append(Token(value, self.line, type))

    def _get_token(self) -> None:
        current = self._advance()
        if current.isidentifier():
            self._handle_identifier()
            self.empty_line = False
        elif self._handle_simple_tokens(current):
            return
        elif current == "<":
            self._add_token(
                TokenType.ASSIGNMENT
                if self._match("-")
                else TokenType.LESS_EQ
                if self._match("=")
                else TokenType.LESS
            )
            self.empty_line = False
        elif current == ">":
            self._add_token(
                TokenType.GREATER_EQ if self._match("=") else TokenType.GREATER
            )
            self.empty_line = False
        elif current == "!":
            if self._match("=", True):
                self._add_token(TokenType.UNEQUAL)
            self.empty_line = False
        elif current == "#":
            self._handle_comments()
        elif current == '"':
            self._handle_string()
            self.empty_line = False
        elif self._is_digit(current):
            self._handle_number()
            self.empty_line = False
        elif current == ":":
            self._handle_block_creation()
        elif current == "\n":
            self._handle_block()
        elif current.isspace():
            self._handle_whitespace()

        # tried all finite automatons but none worked.
        else:
            # TODO: Add error handling here
            print("Tried all automatons. None worked.")

    def _advance(self) -> str:
        self.curr_pos += 1
        return self.text[self.curr_pos - 1]

    def _match(self, char: str, mustMatch: bool = False) -> bool:
        if self.is_eof() or self.text[self.curr_pos] != char:
            if mustMatch:
                pass  # TODO: Add error handling code
            return False
        self.curr_pos += 1
        return True

    def _peek(self) -> str:
        return self.text[self.curr_pos]

    def _handle_simple_tokens(self, char: str) -> bool:
        if self.simple_tokens.get(char, False):
            self._add_token(self.simple_tokens.get(char))
            self.empty_line = False
            return True
        return False

    def _handle_comments(self) -> None:
        while not self.is_eof() and self._peek() != "\n":
            self._advance()

    def _handle_string(self) -> None:
        while not self.is_eof() and self._peek() != '"':
            self._increment_line_counter()
            self._advance()

        if self.is_eof():
            print("Non terminated string.")
            # TODO: Add error handling here
        else:
            self._advance()
            self._add_token(
                TokenType.STRING, self.text[self.start_pos + 1 : self.curr_pos - 1]
            )

    def _increment_line_counter(self) -> None:
        if not self.is_eof() and self._peek() == "\n":
            self.line += 1

    def _is_digit(self, char: str) -> bool:
        """Checks whether char is a number in the range [0,9]."""
        if ord(char) >= 48 and ord(char) <= 57:
            return True
        return False

    def _handle_number(self) -> None:
        while not self.is_eof() and self._is_digit(self._peek()):
            self._advance()
        if not self.is_eof() and self._peek() == ".":
            self._advance()
            while not self.is_eof() and self._is_digit(self._peek()):
                self._advance()
        self._add_token(
            TokenType.NUMBER, float(self.text[self.start_pos : self.curr_pos])
        )

    def _handle_whitespace(self) -> None:
        while not self.is_eof() and self._peek().isspace() and self._peek() != "\n":
            self._advance()

    def _handle_block_creation(self) -> None:
        self._add_token(TokenType.COLON)
        if not self.is_eof() and self._peek() == "\n":
            self._add_token(TokenType.NEWLINE)
            self._increment_line_counter()
            self._advance()
            self.empty_line = True
            # Could also change spaces to be a string an then compare it to another one
            spaces = self._get_num_spaces()
            if spaces > self.indent_pos:
                self.indent_stack.append(self.indent_pos)
                self.indent_pos = spaces
                self._add_token(TokenType.INDENT, self.indent_pos)
            else:
                pass  # TODO: Add error handling "more spaces in after block required"

        else:
            print(f"Newline char must follow block operator {':'}.")
            # TODO: Add error handling as "\n" must follow ":"

    def _get_num_spaces(self) -> int:
        spaces = 0
        while not self.is_eof() and self._peek() == " ":
            spaces += 1
            self._advance()
        return spaces

    def _handle_block(self) -> None:
        if not self.empty_line:
            self._add_token(TokenType.NEWLINE)
        self.line += 1
        spaces = self._get_num_spaces()
        self.empty_line = True
        if spaces == self.indent_pos:  # Same block
            self.empty_line = True
        elif spaces < self.indent_pos:  # Delete block(s)
            while (
                spaces < self.indent_pos
            ):  # comments and empty lines must have same intendation as block level
                self._add_token(TokenType.DEDENT, self.indent_pos)
                self.indent_pos = (
                    0 if not self.indent_stack else self.indent_stack.pop()
                )
        else:
            print(f"Can't indent without {':'}.")
            # TODO: Add error handling can't indent without ':'

    def _handle_identifier(self) -> None:
        while (
            not self.is_eof()
            and (
                self.text[self.start_pos : self.curr_pos] + self._peek()
            ).isidentifier()
        ):
            self._advance()
        identifier = self.text[self.start_pos : self.curr_pos]
        if Lexer.keywords.get(identifier, None):
            self._add_token(Lexer.keywords.get(identifier))
        else:
            self._add_token(TokenType.IDENTIFIER, identifier)
