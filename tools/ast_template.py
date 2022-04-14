from jinja2 import StrictUndefined, Template

template = """from abc import ABC
from src.Lexer import Token
from typing import Any, List

{# Abstract Expression node class -#}
class Expr(ABC):
    pass
    
{% for expr, children in Expr.items() -%}
class {{expr}}(Expr):
    def __init__(self{% for c in children %}, {{c[0]}}: {{c[1]}}{% endfor %}) -> None:
        {% for c in children -%}
        self.{{c[0]}} = {{c[0]}}
        {% endfor %}  
{% endfor -%}

{# Abstract Statement node class -#}
class Stmt(ABC):
    pass
     
{% for stmt, children in Stmt.items() -%}
class {{stmt}}(Stmt):
    {% if children %}
    def __init__(self{% for c in children %}, {{c[0]}}: {{c[1]}}{% endfor %}) -> None:
        {% for c in children -%}
        self.{{c[0]}} = {{c[0]}}
        {% endfor %}  
    {% else %}
        pass
    {% endif %}
{% endfor -%}
"""
nodes = {
    "Expr": {
        "Assign": [("new_var", "bool"), ("name", "Token"), ("expression", "Expr")],
        "SetProperty": [("obj", "Expr"), ("name", "Token"), ("value", "Expr")],
        "BinaryExpr": [("left", "Expr"), ("operator", "Token"), ("right", "Expr")],
        "UnaryExpr": [("operator", "Token"), ("right", "Expr")],
        "GroupingExpr": [("expression", "Expr")],
        "Literal": [("value", "Any")],
        "ObjRef": [("name", "Token")],
        "SuperRef": [("super", "Token"), ("name", "Token")],
        "LogicalExpr": [("left", "Expr"), ("operator", "Token"), ("right", "Expr")],
        "CallExpr": [
            ("callee", "Expr"),
            ("calltoken", "Token"),
            ("args", "List[Expr]"),
        ],
        "PropertyAccess": [("obj", "Expr"), ("name", "Token")],
        "VarAccess": [("name", "Token")],
    },
    "Stmt": {
        "Stmts": [("stmts", "List[Stmt]")],
        "FunctionDecl": [
            ("decorator", "Token"),
            ("name", "Token"),
            ("params", "List[Token]"),
            ("body", "List[Stmt]"),
            ("static", "bool = False"),
        ],
        "ClassDecl": [
            ("name", "Token"),
            ("supercls", "List[VarAccess]"),
            ("methods", "List[Stmt]"),
        ],
        "AssStmt": [("new_var", "bool"), ("name", "Token"), ("expression", "Expr")],
        "ExprStmt": [("expression", "Expr")],
        "BlockStmt": [("stmts", "List[Stmt]")],
        "IfStmt": [("cond", "Expr"), ("then", "BlockStmt"), ("other", "BlockStmt")],
        "WhileStmt": [("cond", "Expr"), ("body", "BlockStmt")],
        "BreakStmt": [],
        "ContinueStmt": [],
        "ReturnStmt": [("err", "Token"), ("expr", "Expr")],
    },
}

if __name__ == "__main__":
    j2_template = Template(template, undefined=StrictUndefined)
    with open("src/ast.py", "w") as f:
        f.write(j2_template.render(nodes))
