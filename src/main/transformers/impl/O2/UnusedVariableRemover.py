from ast import Global, Nonlocal, Constant, Name, Store, Load, stmt, Pass

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


# TODO Added closure function support
class UnusedVariableRemover(ITransformer):
    def __init__(self):
        super().__init__("UnusedVariableRemover", OptimizeLevel.O2)
        # global and nonlocal variables
        self.bypassedVar: set[str] = set()
        # items: varName, codeLine(expr index in body, target index in expr.targets)
        self.assignedVar: set[str] = set()
        # unused but it's the first time to assign
        self.firstAssignedVar: set[str] = set()
        self.usedVar: set[str] = set()

        self.newBody: list[stmt] = []
        self.recheck = False

    def visit_Name(self, node):
        name = node.id
        if name in self.bypassedVar:
            pass
        elif isinstance(node.ctx, Load):
            self.usedVar.add(name)
            if name in self.assignedVar:
                self.assignedVar.remove(name)
        elif isinstance(node.ctx, Store):
            if name not in self.firstAssignedVar:
                self.firstAssignedVar.add(name)
            else:
                self.assignedVar.add(name)

        return self.generic_visit(node)

    def visit_Assign(self, node):
        if not isinstance(node.value, Constant):
            # I think ConstantFolding will turn them into Constant objects.
            # TODO do more checks for magic function override, then we can support more objects
            # Example: __copy__, __deepcopy__, __del__...
            return self.generic_visit(node)

        newTargets = node.targets
        for target in node.targets:
            if not isinstance(target, Name):
                continue
            if not isinstance(target.ctx, Store):
                continue
            if target.id in self.bypassedVar:
                continue
            if self.recheck:
                if target.id not in self.firstAssignedVar:
                    continue
                if target.id in self.usedVar:
                    continue
            else:
                if target.id not in self.assignedVar:
                    continue

            # remove unused assign
            self.done()
            newTargets.remove(target)
        node.targets = newTargets

        if len(newTargets) == 0:
            return None

        return self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if not isinstance(node.target, Name):
            return self.generic_visit(node)
        if not isinstance(node.target.ctx, Store):
            return self.generic_visit(node)
        if node.target.id in self.bypassedVar:
            return self.generic_visit(node)
        if self.recheck:
            if node.target.id not in self.firstAssignedVar:
                return self.generic_visit(node)
            if node.target.id in self.usedVar:
                return self.generic_visit(node)
        else:
            if node.target.id not in self.assignedVar:
                return self.generic_visit(node)

        self.done()
        return None

    def visit_AugAssign(self, node):
        if not isinstance(node.target, Name):
            return self.generic_visit(node)
        if not isinstance(node.target.ctx, Store):
            return self.generic_visit(node)
        if node.target.id in self.bypassedVar:
            return self.generic_visit(node)
        if node.target.id not in self.assignedVar:
            return self.generic_visit(node)

        self.done()
        return None

    def visit_FunctionDef(self, node):
        self.bypassedVar.clear()
        self.assignedVar.clear()
        self.firstAssignedVar.clear()
        self.usedVar.clear()

        self.newBody = node.body
        self.recheck = False
        for i, expr in enumerate(node.body):
            if isinstance(expr, Global) or isinstance(expr, Nonlocal):
                self.bypassedVar.update(expr.names)
                continue

            self.generic_visit(expr)

        node.body = self.newBody
        self.recheck = True

        # re-check
        for expr in node.body:
            self.generic_visit(expr)

        node.body = self.newBody

        self.generic_visit(node)
        if len(node.body) == 0:
            self.done()
            node.body.append(Pass())
        return node
