from jinja2 import StrictUndefined, Template

template = """from abc import ABC
from src.Lexer import Token

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
    def __init__(self{% for c in children %}, {{c[0]}}: {{c[1]}}{% endfor %}) -> None:
        {% for c in children -%}
        self.{{c[0]}} = {{c[0]}}
        {% endfor %}  
{% endfor -%}
"""
nodes = {
    "Expr": {
        "BinaryExpr": [("left", "Expr"), ("operator", "Token"), ("right", "Expr")],
        "UnaryExpr": [("operator", "Token"), ("right", "Expr")],
        "GroupingExpr": [("expression", "Expr")],
        "Literal": [("value", "Token")],
        "Logical": [("left", "Expr"), ("operator", "Token"), ("right", "Expr")],
    },
    "Stmt": {},
}

if __name__ == "__main__":
    j2_template = Template(template, undefined=StrictUndefined)
    with open("src/ast.py", "w") as f:
        f.write(j2_template.render(nodes))
