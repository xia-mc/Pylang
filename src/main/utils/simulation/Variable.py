from __future__ import annotations

from typing import final, TYPE_CHECKING

from pyfastutil.objects import ObjectArrayList
from pylang_annotations import native

if TYPE_CHECKING:
    from utils.simulation.objects.PyObject import PyObject


@native
@final
class Variable:
    """
    Variable object, for Simulation engine.
    """

    __type: list[type]
    __value: list[PyObject]
    __neverUse: bool

    def __init__(self, value: PyObject, type_: type):
        if isinstance(value, ObjectArrayList) and isinstance(type_, ObjectArrayList):  # shadow copy
            self.__value = value
            self.__type = type_
        else:
            self.__value = ObjectArrayList([value], 1)
            self.__type = ObjectArrayList([type_], 1)
        self.__neverUse = True

    def type(self) -> type:
        return self.__type[0]

    def get(self) -> PyObject:
        """Don't change value."""
        self.__neverUse = False
        return self.__value[0]

    def isNeverUse(self) -> bool:
        return self.__neverUse

    def shadow(self) -> Variable:
        """shadow copy"""
        # noinspection PyTypeChecker
        # reason: private init method.
        return Variable(self.__value, self.__type)

    def copy(self) -> Variable:
        """deep copy (variable level)"""
        self.__neverUse = False
        return Variable(self.__value[0], self.__type[0])
