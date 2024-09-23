from abc import ABC, abstractmethod
from ast import NodeTransformer, Module
from typing import final

import Const
from parsers.Source import Source
from transformers.OptimizeLevel import OptimizeLevel


class ITransformer(NodeTransformer, ABC):
    @abstractmethod
    def __init__(self, name: str, level: OptimizeLevel):
        self.logger = Const.logger
        self.name = name
        self.level = level
        self.changes: int = 0

    @final
    def done(self):
        self.changes += 1

    def isChanged(self):
        return self.changes > 0

    @final
    def onRegister(self):
        self._onRegister()

    @final
    def onParseModule(self, module: Module, source: Source):
        self._onParseModule(module, source)

    @final
    def onPreTransform(self):
        self.changes = 0
        self._onPreTransform()

    @final
    def onPostTransform(self):
        self._onPostTransform()

    @final
    def checkLevel(self) -> bool:
        return Const.transManager.level >= self.level

    def _onRegister(self) -> None: ...
    def _onParseModule(self, module: Module, source: Source) -> None: ...
    def _onPreTransform(self) -> None: ...
    def _onPostTransform(self) -> None: ...
