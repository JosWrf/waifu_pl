# Project description

The waifu language will be a dynamically typed toy programming language used to learn more about the internals of an interpreter.
A current version of the grammar is given below.

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
varDecl        → "baka" IDENTIFIER ( "<-" expression )? NEWLINE ;
```

[comment]: <> (after varDecl and statements instead of NEWLINE tokens i should probably also allow EOF tokens aswell.)

### Statements

```ebnf
statement      → exprStmt
               | ifStmt
               | returnStmt
               | whileStmt
               | block ;

exprStmt       → expression NEWLINE;
ifStmt         → "nani" "(" expression ")" block
                 ( "daijobu" block )? ;
returnStmt     → "shinu" expression? "NEWLINE" ;
whileStmt      → "yandere" "(" expression ")" block ;
block          → ":" NEWLINE INDENT declaration* DEDENT;
```

### Expressions

```ebnf
expression     → assignment ;

assignment     → ( call "." )? IDENTIFIER "<-" assignment
               | logic_or ;

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
```

Keywords and their meaning in common programming languages:
{
nani : if statement;
daijobu : else part of if statement;
desu : Function/Method declaration;
baka : Variable declaration;
yandere : While loop;
shinu : Return from function/method;
baito : nil or None or null;
}
