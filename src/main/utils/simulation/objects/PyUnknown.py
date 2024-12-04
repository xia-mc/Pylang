import ast
from typing import Optional

from utils.simulation.Interrupts import EvalException
from utils.simulation.objects.PyObject import PyObject


class PyUnknown(PyObject):

    def getattr(self, name: str) -> PyObject:
        return self

    def setattr(self, name: str, value: PyObject) -> None:
        pass

    def call(self, *args: PyObject, **kwargs: PyObject) -> tuple[PyObject, bool]:
        return PyUnknown(self.engine), False

    def toConstExpr(self) -> Optional[ast.expr]:
        return None

    def toObject(self) -> Optional[object]:
        raise EvalException()
