from __future__ import annotations

from ast import Constant
from types import NoneType
from typing import TypeVar, TYPE_CHECKING

from pylang_annotations import native

from utils.simulation.objects.PyObject import PyObject

if TYPE_CHECKING:
    from utils.simulation.PredictEngine import PredictEngine

T = TypeVar("T", int, float, str, NoneType, type(Ellipsis), type(NotImplemented))


@native
class PyConstant(PyObject):
    def __init__(self, engine: PredictEngine, obj: Constant | T):
        super().__init__(engine)
        self.__value: T = obj.value if isinstance(obj, Constant) else obj
        self.__type: type[T] = type(self.__value)

    def getattr(self, name: str) -> PyObject:
        raise AttributeError(f"'{self.__type}' object has no attribute '{name}'")

    def setattr(self, name: str, value: PyObject) -> None:
        raise AttributeError(f"'{self.__type}' object has no attribute '{name}'")

    def call(self, *args: PyObject, **kwargs: PyObject) -> tuple[PyObject, bool]:
        raise TypeError(f"'{self.__type}' object is not callable")

    def toConstExpr(self) -> Constant:
        return Constant(value=self.__value)

    def toObject(self) -> T:
        return self.__value
