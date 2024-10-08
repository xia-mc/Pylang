import ast
from ast import Global, Nonlocal, Store, Name, Constant, AugAssign, Assign

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class VariableInliner(ITransformer):
    def __init__(self):
        super().__init__("VariableInliner", OptimizeLevel.O2)
        # global and nonlocal variables
        self.bypassedVar: set[str] = set()
        # the variables that can be inline
        self.variables: dict[str, ast.expr] = {}

        self.working = False

    def visit_Name(self, node):
        if not self.working:
            return self.generic_visit(node)
        if isinstance(node.ctx, Store):
            return self.generic_visit(node)
        if node.id in self.variables:
            self.done()
            return ast.copy_location(self.variables[node.id], node)
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if not self.working:
            return self.generic_visit(node)

        node.value = self.generic_visit(node.value)

        for target in node.targets:
            if not isinstance(target, Name):
                continue
            if not isinstance(target.ctx, Store):
                continue
            if not isinstance(node.value, ast.expr):
                continue
            if self.canInline(target, node.value):
                self.variables[target.id] = node.value
            else:
                self.variables.pop(target.id, None)
        return self.generic_visit(node)

    def visit_AugAssign(self, node):
        if not self.working:
            return self.generic_visit(node)

        node.value = self.generic_visit(node.value)

        if isinstance(node.target, Name) and isinstance(node.target.ctx, Store) and isinstance(node.value, ast.expr):
            if self.canInline(node.target, node.value):
                self.variables[node.target.id] = node.value
                self.done()
                return self.generic_visit(self.convert(node))
            else:
                self.variables.pop(node.target.id, None)

        return self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if not self.working:
            return self.generic_visit(node)
        if not isinstance(node.target, Name):
            return self.generic_visit(node)
        if not isinstance(node.target.ctx, Store):
            return self.generic_visit(node)
        if self.canInline(node.target, node.value):
            self.variables[node.target.id] = node.value
            return self.generic_visit(node)
        else:
            self.variables.pop(node.target.id, None)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        outerBypassedVar = self.bypassedVar.copy()
        outerVariables = self.variables.copy()
        outerWorking = self.working

        self.bypassedVar.clear()
        self.variables.clear()
        self.working = True

        for expr in node.body:
            if isinstance(expr, Global) or isinstance(expr, Nonlocal):
                self.bypassedVar.update(expr.names)
                continue

            self.generic_visit(expr)

        self.bypassedVar = outerBypassedVar
        self.variables = outerVariables
        self.working = outerWorking

        return self.generic_visit(node)

    @staticmethod
    def convert(node: AugAssign) -> Assign:
        target = node.target
        value = node.value
        op = node.op

        newValue = ast.BinOp(left=ast.copy_location(target, node), op=op, right=value)

        newNode = ast.Assign(targets=[target], value=newValue)

        return ast.copy_location(newNode, node)

    def canInline(self, name: Name | None, value: ast.expr) -> bool:
        if name is not None and name.id in self.bypassedVar:
            return False
        if isinstance(value, Constant):
            return True
        return False
