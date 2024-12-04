from __future__ import annotations

import ast
from ast import AST
from typing import final, Callable

from pyfastutil.objects import ObjectArrayList

from utils.simulation.Variable import Variable


@final
class Namespace(dict[str, Variable]):
    def __init__(self, parent: AST, namespace: Namespace | dict[str, Variable] = None):
        super().__init__()
        self.parent: AST = parent
        if namespace is not None:
            self.update(namespace)

        self.postTasks: list[Callable] = ObjectArrayList()

    def __repr__(self):
        dic = ""
        for name, var in self.items():
            value = var.get().toConstExpr()
            if value is None:
                dic += f"   {name}: ({var.type().__name__}) Unknown\n"
            else:
                dic += f"   {name}: ({var.type().__name__}) {ast.unparse(value)}\n"

        return "Namespace(\n" f"{dic}" ")"

    def finalize(self):
        for task in self.postTasks:
            task()

    def executeOnPost(self, task: Callable) -> None:
        self.postTasks.append(task)


INamespace = Namespace
