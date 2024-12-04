from __future__ import annotations

from ast import ExceptHandler, Try
from enum import Enum
from typing import TYPE_CHECKING, Optional

from utils.simulation.Namespace import INamespace

if TYPE_CHECKING:
    from utils.simulation.PredictEngine import PredictEngine
    from utils.simulation.objects.PyObject import PyObject


class Type(Enum):
    EXCEPTION = 0
    RETURN = 1


class InterruptContext:
    def __init__(self, engine: PredictEngine, typ: Type, value: PyObject,
                 jmpToNamespace: Optional[INamespace], exceptHandler: Optional[ExceptHandler]):
        self.engine = engine
        self.__type: Type = typ
        self.__value: PyObject = value
        self.__jmpToNamespace: Optional[INamespace] = jmpToNamespace
        self.__exceptHandler: Optional[ExceptHandler] = exceptHandler

    def getType(self) -> Type:
        return self.__type

    def getValue(self) -> PyObject:
        return self.__value

    def isReachTarget(self) -> bool:
        if self.__jmpToNamespace is None:
            return False
        if self.__jmpToNamespace is not self.engine.locals():
            return False
        if not isinstance(self.engine.visiting, Try):
            return False
        return self.__exceptHandler in self.engine.visiting.handlers

    def handle(self) -> None:
        assert self.__type == Type.EXCEPTION
        assert self.isReachTarget()
        self.engine.visit(self.__exceptHandler)


class InterruptManager:
    def __init__(self, engine: PredictEngine):
        self.engine = engine
        self.__context: Optional[InterruptContext] = None

    def getContext(self) -> Optional[InterruptContext]:
        return self.__context

    def finish(self) -> None:
        self.__context = None

    def canInterrupt(self) -> bool:
        return self.__context is None

    def returns(self, value: PyObject) -> None:
        assert self.canInterrupt()
        self.__context = InterruptContext(self.engine, Type.RETURN, value, None, None)

    def throw(self, exception: PyObject, namespace: Optional[INamespace], handler: Optional[ExceptHandler]) -> None:
        assert self.canInterrupt()
        self.__context = InterruptContext(self.engine, Type.EXCEPTION, exception, namespace, handler)


class EvalException(Exception):
    ...
