import ast

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class DeadCodeElimination(ITransformer):
    def __init__(self):
        super().__init__("DeadCodeElimination", OptimizeLevel.O1)

    def visit_If(self, node):
        self.generic_visit(node)

        if isinstance(node.test, ast.Constant):
            if node.test.value:
                return node.body
            else:
                if node.orelse:
                    return node.orelse
                else:
                    return list()
        return node

    def visit_While(self, node):
        self.generic_visit(node)

        if isinstance(node.test, ast.Constant):
            if not node.test.value:
                return list()
        return node

    def visit_IfExp(self, node):
        self.generic_visit(node)

        if isinstance(node.test, ast.Constant):
            if node.test.value:
                return node.body
            else:
                return node.orelse
        return node
