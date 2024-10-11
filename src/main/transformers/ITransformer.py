from abc import ABC, abstractmethod
from ast import NodeTransformer, Module
from typing import final

import Const
from utils.Source import Source
from transformers.OptimizeLevel import OptimizeLevel


class ITransformer(NodeTransformer, ABC):
    @abstractmethod
    def __init__(self, name: str, level: OptimizeLevel):
        self.logger = Const.logger
        self.name = name
        self.level = level
        self.changed = False

    @final
    def done(self):
        self.changed = True

    def isChanged(self):
        return self.changed

    @final
    def onRegister(self):
        self._onRegister()

    @final
    def onParseModule(self, module: Module, source: Source):
        self._onParseModule(module, source)

    @final
    def onPreTransform(self):
        self.changed = False
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
