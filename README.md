# Project description

> The waifu language will be a dynamically typed toy programming language used to learn more about the internals of an interpreter.
> A current version of the grammar is given below.

## Syntax Grammar

```ebnf
program        → declaration* EOF ;
```

### Declarations

```ebnf
declaration    → funDecl
               | varDecl
               | statement ;

funDecl        → "desu" function ;
```

[comment]: <> (after varDecl and statements instead of NEWLINE tokens i should probably also allow EOF tokens aswell.)

### Statements

```ebnf
statement      → exprStmt
               | ifStmt
               | assignStmt
               | returnStmt
               | whileStmt;

exprStmt       → expression NEWLINE;
assignStmt     → (call ".")? IDENTIFIER "<-" assign NEWLINE;
ifStmt         → "nani" "(" expression ")" block
                 ( "daijobu" block )? ;
returnStmt     → "shinu" expression? "NEWLINE" ;
whileStmt      → "yandere" "(" expression ")" block ;
block          → ":" NEWLINE INDENT declaration+ DEDENT;

assign         → (call ".")? IDENTIFIER "<-" assign;
               | expression
```

### Expressions

```ebnf
expression     → logic_or ;

logic_or       → logic_and ( "or" logic_and )* ;
logic_and      → equality ( "and" equality )* ;
equality       → comparison ( ( "!=" | "=" ) comparison )* ;
comparison     → term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
term           → factor ( ( "-" | "+" ) factor )* ;
factor         → unary ( ( "/" | "*" ) unary )* ;

unary          → ( "not" | "-" ) unary | call ;
call           → primary ( "(" arguments? ")" | "." IDENTIFIER )* ;
primary        → "true" | "false" | "baito"
               | NUMBER | STRING | IDENTIFIER | "(" expression ");

function       → IDENTIFIER "(" parameters? ")" block;
parameters     → IDENTIFIER "(" "," IDENTIFIER* ")";
arguments      → expression "(" "," expression* ")";
```

## Language specifics

**Keywords and their meaning in other programming languages:**

| waifu keyword |           meaning           |
| ------------- | :-------------------------: |
| nani          |        if statement         |
| daijobu       |  else part of if statement  |
| desu          | function/method declaration |
| baka          |    variable declaration     |
| yandere       |         while loop          |
| shinu         |      return statement       |
| baito         |         null value          |
