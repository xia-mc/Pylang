import ast
from abc import ABC, abstractmethod
from ast import NodeTransformer, Module
from typing import final, Optional

from colorama import Fore

import Const
from log.Logger import Logger
from utils.Source import Source
from ast import AST
from transformers.OptimizeLevel import OptimizeLevel


class ITransformer(NodeTransformer, ABC):
    @abstractmethod
    def __init__(self, name: str, level: OptimizeLevel):
        self.logger = Const.logger
        self.name = name
        self.level = level
        self._changed = False
        self._flags: set[tuple[str, Optional[AST]]] = set()

    @final
    def done(self):
        self._changed = True

    def isChanged(self):
        return self._changed

    @final
    def onRegister(self):
        self._onRegister()

    @final
    def onParseModule(self, module: Module, source: Source):
        self._onParseModule(module, source)

    @final
    def onPreTransform(self):
        self._changed = False
        self._onPreTransform()

    @final
    def onPostTransform(self):
        self._onPostTransform()

    @final
    def checkLevel(self) -> bool:
        return Const.transManager.level >= self.level

    @final
    def flag(self, message: BaseException | str, node: AST = None) -> None:
        """
        Log a warning with a specific message format for possible exceptions.

        :param message: The exception details.
        :param node: the AST object visiting
        """
        if isinstance(message, BaseException):
            message = f"{type(message).__name__}: {str(message)}"

        flagData = message, node
        if flagData in self._flags:
            # prevert to spam flag messages
            return
        self._flags.add(flagData)

        source = Const.transManager.getCurrentSource()
        extraMsg = "?"
        if node is not None:
            extraMsg = str(node.lineno)
            extraMsg += '\n' + Fore.CYAN

            codeLine = source.getSourceLines()[node.lineno - 1]
            flagBlock = ast.unparse(node)
            codeLine = codeLine.replace(
                flagBlock,
                Fore.LIGHTCYAN_EX + Logger.UNDERLINE + flagBlock + Logger.RESET + Fore.CYAN)
            extraMsg += codeLine

        self.logger.warn(f"{Fore.YELLOW}Possible exception in "
                         f"{Fore.CYAN}{source.getFilename()}"
                         f"{Fore.RESET}:"
                         f"{Fore.CYAN}{extraMsg}"
                         f"\n{Fore.RED}{message}.")

    def _onRegister(self) -> None:
        ...

    def _onParseModule(self, module: Module, source: Source) -> None:
        ...

    def _onPreTransform(self) -> None:
        ...

    def _onPostTransform(self) -> None:
        ...
