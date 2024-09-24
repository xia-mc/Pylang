import ast
from ast import Str, Expr, Pass

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class DocumentRemover(ITransformer):
    def __init__(self):
        super().__init__("DocumentRemover", OptimizeLevel.O1)

    def visit_FunctionDef(self, node):
        self.generic_visit(node)

        node.type_comment = None
        node.returns = None
        node.body = [stmt for stmt in node.body if not isinstance(stmt, Expr) or not isinstance(stmt.value, Str)]

        if len(node.body) == 0:
            node.body.append(Pass())
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)

        node.body = [stmt for stmt in node.body if not isinstance(stmt, Expr) or not isinstance(stmt.value, Str)]

        if len(node.body) == 0:
            node.body.append(Pass())
        return node

    def visit_Module(self, node):
        self.generic_visit(node)

        node.body = [stmt for stmt in node.body if not isinstance(stmt, Expr) or not isinstance(stmt.value, Str)]

        if len(node.body) == 0:
            node.body.append(Pass())
        return node
