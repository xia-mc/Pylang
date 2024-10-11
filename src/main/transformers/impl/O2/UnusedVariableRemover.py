from ast import Global, Nonlocal, Constant, Name, Store, Load, stmt, Pass, Del
from enum import Enum

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel


class State(Enum):
    NONE = 0
    FIRST = 1
    SECOND = 2
    BYPASS_VAR = 3


class UnusedVariableRemover(ITransformer):
    def __init__(self):
        super().__init__("UnusedVariableRemover", OptimizeLevel.O2)
        # global and nonlocal variables
        self.bypassedVar: set[str] = set()
        # while loop test variables
        self.tmpBypassedVar: set[str] = set()
        # varName
        self.assignedVar: set[str] = set()
        # unused but it's the first time to assign
        self.firstAssignedVar: set[str] = set()
        self.usedVar: set[str] = set()

        self.newBody: list[stmt] = []
        self.state: State = State.NONE

    def shouldBypass(self, name: str) -> bool:
        """
        Should we bypass the var?
        :param name: var name
        :return: true -> bypass
        """
        if name in self.bypassedVar:
            return True
        if name in self.tmpBypassedVar:
            return True
        match self.state:
            case State.FIRST:
                # if name not in self.assignedVar:
                return True
            case State.SECOND:
                if name not in self.firstAssignedVar:
                    return True
                if name in self.usedVar:
                    return True
            case State.BYPASS_VAR:
                return True
        return False

    def visit_Name(self, node):
        if self.state is State.NONE:
            return self.generic_visit(node)

        name = node.id
        if name in self.bypassedVar:
            return self.generic_visit(node)

        if self.state is State.BYPASS_VAR:
            self.tmpBypassedVar.add(name)
        if isinstance(node.ctx, Load):
            self.usedVar.add(name)
            if name in self.assignedVar:
                self.assignedVar.remove(name)
        elif isinstance(node.ctx, Store):
            if name not in self.firstAssignedVar:
                self.firstAssignedVar.add(name)
            else:
                self.assignedVar.add(name)
        elif isinstance(node.ctx, Del):
            self.usedVar.discard(name)
            self.assignedVar.discard(name)
            self.firstAssignedVar.discard(name)

        return self.generic_visit(node)

    def visit_Assign(self, node):
        if self.state is State.NONE:
            return self.generic_visit(node)
        if not isinstance(node.value, Constant):
            return self.generic_visit(node)

        newTargets = node.targets
        for target in node.targets:
            if not isinstance(target, Name):
                continue
            if not isinstance(target.ctx, Store):
                continue
            if self.shouldBypass(target.id):
                continue

            # remove unused assign
            self.done()
            newTargets.remove(target)
        node.targets = newTargets

        if len(newTargets) == 0:
            return None

        return self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if self.state is State.NONE:
            return self.generic_visit(node)
        if not isinstance(node.value, Constant):
            return self.generic_visit(node)

        if not isinstance(node.target, Name):
            return self.generic_visit(node)
        if not isinstance(node.target.ctx, Store):
            return self.generic_visit(node)
        if self.shouldBypass(node.target.id):
            return self.generic_visit(node)

        self.done()
        return None

    def visit_AugAssign(self, node):
        if self.state is State.NONE:
            return self.generic_visit(node)
        if not isinstance(node.value, Constant):
            return self.generic_visit(node)

        if not isinstance(node.target, Name):
            return self.generic_visit(node)
        if not isinstance(node.target.ctx, Store):
            return self.generic_visit(node)
        if self.shouldBypass(node.target.id):
            return self.generic_visit(node)

        self.done()
        return None

    def visit_For(self, node):
        if self.state is State.NONE:
            return self.generic_visit(node)
        # Check the target of the loop
        if isinstance(node.target, Name) and isinstance(node.target.ctx, Store):
            self.assignedVar.add(node.target.id)

        # Visit the loop body to track variable usage
        self.generic_visit(node)

        return node

    def visit_While(self, node):
        if self.state is State.NONE:
            return self.generic_visit(node)
        # Visit the loop body to track variable usage
        lastState = self.state
        self.state = State.BYPASS_VAR
        self.generic_visit(node.test)

        self.generic_visit(node)
        self.state = lastState
        self.tmpBypassedVar.clear()
        return node

    def visit_FunctionDef(self, node):
        # Save outer scope variables before entering the new function (for closure support)
        outerBypassed = self.bypassedVar.copy()
        outerTmpBypassed = self.tmpBypassedVar.copy()
        outerAssigned = self.assignedVar.copy()
        outerFirstAssigned = self.firstAssignedVar.copy()
        outerUsed = self.usedVar.copy()
        outerState = self.state

        self.bypassedVar.clear()
        self.tmpBypassedVar.clear()
        self.assignedVar.clear()
        self.firstAssignedVar.clear()
        self.usedVar.clear()
        self.state = State.FIRST

        # Process the current function's body
        self.newBody = node.body
        for expr in node.body:
            if isinstance(expr, Global) or isinstance(expr, Nonlocal):
                self.bypassedVar.update(expr.names)
                continue
            self.generic_visit(expr)

        node.body = self.newBody
        self.state = State.SECOND

        # Re-check the function body after the first pass
        for expr in node.body:
            self.generic_visit(expr)

        # Remove variables that were first assigned but never used
        unused_vars = self.firstAssignedVar - self.usedVar
        for var in unused_vars:
            self.assignedVar.discard(var)

        node.body = self.newBody

        # Remove useless pass
        self.newBody = []
        for expr in node.body:
            if isinstance(expr, Pass) and len(node.body) > 1:
                continue
            self.newBody.append(expr)
        node.body = self.newBody

        # Restore outer scope variables after processing the closure
        self.bypassedVar = outerBypassed
        self.tmpBypassedVar = outerTmpBypassed
        self.assignedVar = outerAssigned
        self.firstAssignedVar = outerFirstAssigned
        self.usedVar = outerUsed
        self.state = outerState

        return self.generic_visit(node)

    def visit_Lambda(self, node):
        if self.state is State.NONE:
            return self.generic_visit(node)
        # Lambda functions are much simpler than function definitions
        # We only need to visit the arguments and body (a single expression)

        # Save outer scope variables before entering the lambda (for closure support)
        outerBypassed = self.bypassedVar.copy()
        outerTmpBypassed = self.tmpBypassedVar.copy()
        outerAssigned = self.assignedVar.copy()
        outerFirstAssigned = self.firstAssignedVar.copy()
        outerUsed = self.usedVar.copy()
        outerState = self.state

        # Visit lambda arguments
        for arg in node.args.args:
            if isinstance(arg, Name):
                self.assignedVar.add(arg.id)

        # Visit lambda body
        self.generic_visit(node.body)

        # Restore outer scope variables after processing the closure
        self.bypassedVar = outerBypassed
        self.tmpBypassedVar = outerTmpBypassed
        self.assignedVar = outerAssigned
        self.firstAssignedVar = outerFirstAssigned
        self.usedVar = outerUsed
        self.state = outerState

        return node
