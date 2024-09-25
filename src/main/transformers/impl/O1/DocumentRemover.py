from ast import Str, Expr, Pass, Assign

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class DocumentRemover(ITransformer):
    def __init__(self):
        super().__init__("DocumentRemover", OptimizeLevel.O1)

    def visit_AnnAssign(self, node):
        self.generic_visit(node)

        self.done()
        if node.value is not None:
            assign_node = Assign(
                targets=[node.target],
                value=node.value
            )
            return assign_node
        else:
            return None

    def visit_FunctionDef(self, node):
        self.generic_visit(node)

        for arg in node.args.args:
            if arg.annotation:
                self.done()
                arg.annotation = None
        for arg in node.args.kwonlyargs:
            if arg.annotation:
                self.done()
                arg.annotation = None
        if node.args.vararg:
            if node.args.vararg.annotation:
                self.done()
                node.args.vararg.annotation = None
        if node.args.kwarg:
            if node.args.vararg.annotation:
                self.done()
                node.args.kwarg.annotation = None

        if node.type_comment:
            self.done()
            node.type_comment = None
        if node.returns:
            self.done()
            node.returns = None

        newBody = []
        for stmt in node.body:
            if not isinstance(stmt, Expr) or not isinstance(stmt.value, Str):
                newBody.append(stmt)
            else:
                self.done()
        node.body = newBody

        if len(node.body) == 0:
            self.done()
            node.body.append(Pass())
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)

        newBody = []
        for stmt in node.body:
            if not isinstance(stmt, Expr) or not isinstance(stmt.value, Str):
                newBody.append(stmt)
            else:
                self.done()
        node.body = newBody

        if len(node.body) == 0:
            self.done()
            node.body.append(Pass())
        return node

    def visit_Module(self, node):
        self.generic_visit(node)

        newBody = []
        for stmt in node.body:
            if not isinstance(stmt, Expr) or not isinstance(stmt.value, Str):
                newBody.append(stmt)
            else:
                self.done()
        node.body = newBody

        if len(node.body) == 0:
            self.done()
            node.body.append(Pass())
        return node
