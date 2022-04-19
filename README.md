# Project description

> The waifu language will be a dynamically typed toy programming language used to learn more about the internals of an interpreter.
> A current version of the grammar is given below.

## Syntax Grammar

```ebnf
program        → import* declaration* EOF ;
import         → "gaijin" qualifiedname NEWLINE ;
```

### Declarations

```ebnf
declaration    → funDecl
               | classDecl
               | varDecl
               | statement ;

funDecl        → decorator? function ;
classDecl      → "waifu" IDENTIFIER ("neesan" IDENTIFIER ("," IDENTIFIER)*)?
                ":" NEWLINE INDENT function* DEDENT;
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
assignStmt     → ("baka")? (call ".")? IDENTIFIER "<-" assign NEWLINE;
ifStmt         → "nani" expression block
                 ( "daijobu" block )? ;
returnStmt     → "shinu" expression? "NEWLINE" ;
breakStmt      → "yamero" "NEWLINE" ;
continueStmt   → "kowai" "NEWLINE" ;
whileStmt      → "yandere" expression block ;
block          → ":" NEWLINE INDENT declaration+ DEDENT;

assign         → (call ".")? IDENTIFIER "<-" assign;
               | expression
```

### Expressions

```ebnf
expression     → lambda ;

lambda         → "?" parameters ":" lambda ;
               | logic_or ;
logic_or       → logic_and ( "or" logic_and )* ;
logic_and      → equality ( "and" equality )* ;
equality       → comparison ( ( "!=" | "=" ) comparison )* ;
comparison     → term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
term           → factor ( ( "-" | "+" ) factor )* ;
factor         → unary ( ( "/" | "*" ) unary )* ;

unary          → ( "not" | "-" ) unary | call ;
call           → primary ( "(" arguments? ")" | "." IDENTIFIER )* ;
primary        → "true" | "false" | "baito" | "watashi" | "haha" "." IDENTIFIER
               | NUMBER | STRING | IDENTIFIER | "(" expression ");

function       → ("desu" | "oppai") IDENTIFIER "(" parameters? ")" block;
parameters     → IDENTIFIER ( "," IDENTIFIER* );
arguments      → expression ( "," expression* );
decorator      → "@" IDENTIFIER NEWLINE;
qualifiedname  → ( "." )* IDENTIFIER ( "." IDENTIFIER )*;
```

## Language specifics

**Keywords and their meaning in other programming languages:**

| waifu keyword |                   meaning                   |
| ------------- | :-----------------------------------------: |
| nani          |                if statement                 |
| daijobu       |          else part of if statement          |
| desu          |         function/method declaration         |
| yandere       |                 while loop                  |
| shinu         |              return statement               |
| baito         |                 null value                  |
| baka          |   make new local variable when assigning    |
| yamero        |               break statement               |
| kowai         |             continue statement              |
| watashi       |         reference to current object         |
| shison        |                 constructor                 |
| oppai         | static method that can be called on a class |
| neesan        |               extends clause                |
| haha          | get access to superclass properties (super) |
| gaijin        |               import keyword                |

> Use baka to declare a new local variable otherwise an assignment will assign to a variable in the surrounding scope or define one
> in the current scope if none with that name could be found.
> Only use oppai for class methods.

### Inheritance

Instead of a single superclass a list of superclasses is bound to the surrounding scope of the surrounding scope of method body using super.
When querying methods, the first superclass in the list is preferred. That means if A inherits from B and C and finds a superclass method in B, it always returns this method. Even if C has a method with the same name. The same holds true for class methods. The search continues until all superclasses and their superclasses have been searched through or a method has been found.

```python
waifu A:
    desu shison():
        print("In A")

waifu B neesan A:
    desu shison():
        print("In B")
    oppai big():
        print("Big in B")

waifu C neesan A:
    desu shison():
        print("In C")

    oppai big():
        print("Big in C")

waifu D neesan C,B:
    desu shison():
        print("In D")
        haha.shison()

d <- D()
# Prints:
# In D
# In C
D.big()
# Prints:
# Big in C
```

### Modules

Every .waifu file will be considered a module.
Imports have to be at the first statements appearing in a module.
(I never experienced a case where this would be restrictive, so i will enforce it here.)
There are two ways modules are searched for:

1. If the qualified name starts with '.', then path will be calculated relative with respect to the absolute path of the importing module (currently active module).

2. If the name does not start with '.', then the importing name will be appended to the current working directory.

Note: In both cases .waifu will be added to the calculated name.

All global elements defined within the module will be exported from the imported module. This is to prevent transitive copying.
