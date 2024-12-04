import random
from ast import Global, Nonlocal, Store, FunctionDef, Name
from enum import Enum

from pyfastutil.objects import ObjectArrayList

from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel
from utils.eval.CythonCompiler import CythonCompiler


class State(Enum):
    NONE = 0
    SEARCH = 1
    REMAP = 2


class VariableRenamer(ITransformer):
    # mapping from number to name
    # noinspection SpellCheckingInspection
    NAME_MAP: list[str] = ObjectArrayList("Il")

    def __init__(self):
        super().__init__("VariableRenamer", OptimizeLevel.O2)
        # global and nonlocal variables
        self.bypassedVar: set[str] = set()
        # the mapping for variable names (old, new)
        self.mapping: dict[str, str] = {}
        # assigned names counter
        self.assigned = len(VariableRenamer.NAME_MAP) ** 5
        # TODO i need to fix it
        self.ignoring = False

        self.state = State.NONE

    def _onPreTransform(self) -> None:
        self.assigned = len(VariableRenamer.NAME_MAP) ** 5

    def visit_Name(self, node):
        match self.state:
            case State.SEARCH:
                if not isinstance(node.ctx, Store):
                    return self.generic_visit(node)
                if self.ignoring:
                    return self.generic_visit(node)
                if node.id in self.bypassedVar:
                    return self.generic_visit(node)
                if node.id in self.mapping:
                    return self.generic_visit(node)

                newName = self.generateName()
                self.mapping[node.id] = newName
            case State.REMAP:
                if node.id not in self.mapping:
                    return self.generic_visit(node)

                node.id = self.mapping[node.id]

        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        outerBypassed = self.bypassedVar.copy()
        outerMapping = self.mapping.copy()
        outerAssigned = self.assigned
        outerState = self.state

        self.state = State.NONE

        for arg in node.args.args:
            # works wrongly when call with kwargs
            # newName = self.generateName()
            newName = arg.arg
            self.mapping[arg.arg] = newName
            arg.arg = newName

        self.state = State.SEARCH

        for expr in node.body:
            if isinstance(expr, Global) or isinstance(expr, Nonlocal):
                self.bypassedVar.update(expr.names)
                continue
            if isinstance(expr, FunctionDef):
                continue

            self.generic_visit(expr)

        self.state = State.REMAP
        for expr in node.body:
            self.generic_visit(expr)

        self.state = State.NONE
        self.bypassedVar = outerBypassed
        self.mapping = outerMapping
        # self.assigned = outerAssigned
        self.state = outerState

        return self.generic_visit(node)

    def visit_ListComp(self, node):
        return self.handleIgnore(node)

    def visit_SetComp(self, node):
        return self.handleIgnore(node)

    def visit_DictComp(self, node):
        return self.handleIgnore(node)

    def visit_Lambda(self, node):
        return node

    def handleIgnore(self, node):
        self.ignoring = True
        self.generic_visit(node)
        self.ignoring = False
        return node

    def generateName(self) -> str:
        self.assigned += 1
        result = ""
        count = self.assigned

        while count > 0:
            nextInt = (count - 1) % len(self.NAME_MAP)
            result = self.NAME_MAP[nextInt] + result
            count = (count - 1) // len(self.NAME_MAP)

        return result if CythonCompiler.isValidImportName(result) else self.generateName()
