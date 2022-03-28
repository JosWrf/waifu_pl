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
        "BinaryExpr": [("left", "Expr"), ("operator", "Token"), ("right", "Expr")],
        "UnaryExpr": [("operator", "Token"), ("right", "Expr")],
        "GroupingExpr": [("expression", "Expr")],
        "Literal": [("value", "Any")],
        "LogicalExpr": [("left", "Expr"), ("operator", "Token"), ("right", "Expr")],
        "VarAccess": [("name", "Token")],
    },
    "Stmt": {
        "Stmts": [("stmts", "List[Stmt]")],
        "AssStmt": [("new_var", "bool"), ("name", "Token"), ("expression", "Expr")],
        "ExprStmt": [("expression", "Expr")],
        "BlockStmt": [("stmts", "List[Stmt]")],
        "IfStmt": [("cond", "Expr"), ("then", "BlockStmt"), ("other", "BlockStmt")],
        "WhileStmt": [("cond", "Expr"), ("body", "BlockStmt")],
        "BreakStmt": [],
        "ContinueStmt": [],
    },
}

if __name__ == "__main__":
    j2_template = Template(template, undefined=StrictUndefined)
    with open("src/ast.py", "w") as f:
        f.write(j2_template.render(nodes))
