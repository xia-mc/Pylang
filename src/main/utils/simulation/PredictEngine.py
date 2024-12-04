from __future__ import annotations

import builtins
import typing
from abc import ABC, abstractmethod
from ast import Name, AST, FunctionDef, ClassDef, ExceptHandler
from collections import deque
from types import NoneType
from typing import Optional, TypeVar

from pyfastutil.objects import ObjectArrayList
from pylang_annotations import native

import Const
from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel
from utils.ASTUtils import ASTUtils
from utils.eval.PureFunctions import PureFunctions
from utils.simulation.Interrupts import InterruptManager, Type
from utils.simulation.Namespace import Namespace, INamespace
from utils.simulation.objects.PyObject import PyObject
from utils.simulation.Variable import Variable
from utils.simulation.objects.PyConstant import PyConstant
from utils.simulation.objects.PyUnknown import PyUnknown

T = TypeVar("T", bound=AST)


@native
class PredictEngine(ITransformer, ABC):
    # noinspection PyTypeChecker
    def __init__(self):
        super().__init__("PredictEngine", OptimizeLevel.O3)
        self.__builtins: INamespace = None
        self.__locals: INamespace = None
        self.__globals: INamespace = None
        self.__nameStack: list[INamespace] = None
        self.__exceptStack: deque[dict[PyObject, tuple[INamespace, ExceptHandler]]] = None
        self.visiting: Optional[AST] = None
        self.interruptManager: InterruptManager = None

    def reset(self, parent: AST) -> None:
        self.__builtins: INamespace = Namespace(parent)
        for name in dir(builtins):
            attr: object = getattr(builtins, name)
            if callable(attr) and not PureFunctions.isPure(attr):  # bypass eg: print, input
                var = Variable(PyUnknown(self), type(attr))
            else:
                var = Variable(ASTUtils.toPyObject(self, attr), type(attr))

            var.get()  # Bypass unused remover
            self.__builtins[name] = var

        self.__globals: INamespace = Namespace(parent)
        # TODO recode this after support class object
        self.__globals["__builtins__"] = Variable(PyUnknown(self), object)
        self.__globals["__doc__"] = Variable(PyConstant(self, None), NoneType)
        self.__globals["__loader__"] = Variable(PyUnknown(self), object)
        self.__globals["__name__"] = Variable(PyUnknown(self), str)
        self.__globals["__package__"] = Variable(PyUnknown(self), str)
        self.__globals["__spec__"] = Variable(PyUnknown(self), object)

        self.__locals: INamespace = self.__globals
        self.__nameStack: list[INamespace] = ObjectArrayList([self.__globals], 3)
        self.__exceptStack: deque[dict[Name, tuple[INamespace, AST]]] = deque()
        self.__exceptStack.append(dict())
        self.visiting: Optional[AST] = None
        self.interruptManager: InterruptManager = InterruptManager(self)

    def locals(self) -> INamespace:
        """Don't modify namespace."""
        return self.__locals

    def globals(self) -> INamespace:
        """Don't modify namespace."""
        return self.__globals

    def builtins(self) -> INamespace:
        """Don't modify namespace."""
        return self.__builtins

    def pushMatrix(self) -> None:
        matrix = Namespace(self.visiting)
        self.__nameStack.append(matrix)
        self.__locals = matrix
        self.__exceptStack.append(self.__exceptStack[-1])

    def popMatrix(self) -> None:
        assert len(self.__nameStack) > 1
        self.__locals.finalize()
        self.__nameStack.pop()
        self.__locals = self.__nameStack[-1]
        self.__exceptStack.pop()

    def put(self, name: str, var: Variable) -> None:
        self.__locals[name] = var.copy()

    def get(self, name: str) -> Variable:
        if name in self.__locals:
            return self.__locals[name]
        for namespace in self.__nameStack[:-1][::-1]:
            if name in namespace:
                return namespace[name]
        if name in self.__builtins:
            return self.__builtins[name]
        self.throw(NameError(f"'{name}' is not defined."))

    def throw(self, exception: PyObject | Exception) -> None:
        if isinstance(exception, Exception):
            self.throw(ASTUtils.toPyObject(self, exception))

        for handlers in reversed(self.__exceptStack):
            if exception not in handlers:
                continue
            handler = handlers[exception]
            self.interruptManager.throw(exception, handler[0], handler[1])
            return None
        self.interruptManager.throw(exception, None, None)  # stop simulation
        self.flag(f"(Simulation) {exception.type().__name__}: {str(exception.toObject())}", self.visiting)
        return None

    def _onPreTransform(self) -> None:
        self.reset(Const.transManager.getCurrentModule())

    def _onPostTransform(self) -> None:
        self.__globals.finalize()

    def visit(self, node: T) -> T:
        interrupt = self.interruptManager.getContext()
        if interrupt is not None and interrupt.getType() == Type.EXCEPTION:
            if not interrupt.isReachTarget():
                return super().visit(node)
            interrupt.handle()

        self.visiting = node

        node = self._visit(node)

        self.visiting = node

        if type(node) in (FunctionDef, ClassDef):
            # try:
            #     node = super().visit(node)
            # except Exception as ignored:
            #     typing.cast(..., ignored)
            #     ...
            # self.interruptManager.finish()
            return node

        return super().visit(node)

    @abstractmethod
    def _visit(self, node: T) -> T:
        ...
