from __future__ import annotations

import ast
from typing import Optional, TYPE_CHECKING

from utils.ASTUtils import ASTUtils
from utils.simulation.Interrupts import EvalException

if TYPE_CHECKING:
    from utils.simulation.PredictEngine import PredictEngine


class PyObject:

    def __init__(self, engine: PredictEngine):
        self.engine = engine
        self._attrs: dict[str, PyObject] = dict()

    def getattr(self, name: str) -> PyObject:
        if name not in self._attrs:
            raise AttributeError(f"Object has no attribute '{name}'")
        return self._attrs[name]

    def setattr(self, name: str, value: PyObject) -> None:
        self._attrs[name] = value

    def call(self, *args: PyObject, **kwargs: PyObject) -> tuple[PyObject, bool]:
        raise TypeError(f"object is not callable")

    def toConstExpr(self) -> Optional[ast.expr]:
        return None

    def toObject(self) -> object:
        raise EvalException()

    def type(self) -> type:
        try:
            obj = self.toObject()
            return type(obj)
        except EvalException:
            return object

    def __call__(self, *args: object, **kwargs: object) -> object:
        args: tuple[PyObject, ...] = tuple(ASTUtils.toPyObject(self.engine, arg) for arg in args)
        kwargs: dict[str, PyObject] = {key: ASTUtils.toPyObject(self.engine, value) for key, value in
                                       kwargs}

        return self.call(*args, **kwargs)[0].toObject()
