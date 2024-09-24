import ast
from _ast import stmt
from ast import Str, Expr, Pass, Assign, Global, Nonlocal, Constant, Name, Store, Load, AST
from typing import SupportsIndex, Union

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class UnusedVariableRemover(ITransformer):
    def __init__(self):
        super().__init__("UnusedVariableRemover", OptimizeLevel.O2)
        self.usedVar: set[str] = set()  # varNames

    def visit_Name(self, node):
        self.generic_visit(node)

        if isinstance(node.ctx, Load):
            self.usedVar.add(node.id)
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)

        # global and nonlocal variables
        bypassedVar: set[str] = set()
        # items: varName, codeLine(expr index in body, target index in expr.targets)
        unusedAssign: dict[str, tuple[SupportsIndex, SupportsIndex]] = {}
        modifiedAssign: set[Assign] = set()

        for bodyIndex in range(len(node.body)):
            expr: AST | stmt = node.body[bodyIndex]  # I use the union typing to bypass linter

            if isinstance(expr, Global) or isinstance(expr, Nonlocal):
                bypassedVar.update(expr.names)
                continue

            self.usedVar.clear()
            self.generic_visit(expr)

            for var in self.usedVar:
                if var in unusedAssign:
                    del unusedAssign[var]

            if isinstance(expr, Assign):
                if not isinstance(expr.value, Constant):
                    # I think ConstantFolding will turn them into Constant objects.
                    continue

                self.logger.debug(expr.targets, expr.targets[0].id)
                for targetIndex in range(len(expr.targets)):
                    target = expr.targets[targetIndex]

                    if not isinstance(target, Name):
                        continue
                    if not isinstance(target.ctx, Store):  # I think it's 100% Store
                        continue

                    name = target.id
                    if name in bypassedVar:
                        continue
                    if name in unusedAssign:
                        self.done()
                        self.logger.debug("Done")
                        # remove last assign
                        bodyId, targetId = unusedAssign[name]

                        # to bypass my linter
                        body: list[Assign | stmt] = node.body
                        assign: Assign = body[bodyId]
                        targets: list[Union[expr, None]] = assign.targets
                        targets[targetId] = None
                        modifiedAssign.add(assign)
                    unusedAssign[name] = bodyIndex, targetIndex
                    self.logger.debug(unusedAssign)

        newBody: list[stmt] = []
        for expr in node.body:
            if isinstance(expr, Assign) and expr in modifiedAssign:
                newTargets: list[expr] = []
                for target in expr.targets:
                    if target is not None:
                        newTargets.append(target)
                expr.targets = newTargets

                if len(expr.targets) == 0:
                    continue
            newBody.append(expr)

        node.body = newBody
        return node
