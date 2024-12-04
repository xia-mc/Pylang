import ast
from abc import ABC, abstractmethod
from ast import NodeTransformer, Module
from typing import final, Optional

from colorama import Fore

import Const
from log.Logger import Logger
from utils.source.CodeSource import CodeSource
from ast import AST
from transformers.OptimizeLevel import OptimizeLevel


class ITransformer(NodeTransformer, ABC):
    @abstractmethod
    def __init__(self, name: str, level: OptimizeLevel, post: bool = False):
        self.logger = Const.logger
        self.name = name
        self.level = level
        self._changed = False
        self._flags: set[tuple[str, Optional[tuple[AST, ...]]]] = set()
        self.post = post

    def done(self):
        self._changed = True

    def isChanged(self):
        return self._changed

    @final
    def init(self):
        self._init()

    @final
    def onParseModule(self, module: Module, source: CodeSource):
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
    def flag(self, message: BaseException | str, node: AST = None, *extraNodes: AST) -> None:
        """
        Log a warning with a specific message format for possible exceptions.

        :param message: The exception details.
        :param node: the AST objects visiting.
        :param extraNodes: others nodes for linting.
        """
        if isinstance(message, BaseException):
            message = f"{type(message).__name__}: {str(message)}"

        flagData = message, (node,) + extraNodes
        if flagData in self._flags:
            # prevert to spam flag messages
            return
        self._flags.add(flagData)

        # Const.transManager.updateSources()
        source = Const.transManager.getCurrentSource()
        extraMsg = "?"
        if node is not None:
            extraMsg = str(node.lineno)
            extraMsg += '\n' + Fore.CYAN

            codeLine = source.getSourceLines()[node.lineno - 1]
            flagBlocks = (ast.unparse(n) for n in (node,) + extraNodes)
            for flagBlock in flagBlocks:
                codeLine = codeLine.replace(
                    flagBlock,
                    Fore.LIGHTCYAN_EX + Logger.UNDERLINE + flagBlock + Logger.RESET + Fore.CYAN)
            extraMsg += codeLine

        self.logger.warn(f"{Fore.YELLOW}Possible exception in "
                         f"{Fore.CYAN}{source.getFilepath()}"
                         f"{Fore.RESET}:"
                         f"{Fore.CYAN}{extraMsg}"
                         f"\n{Fore.RED}{message}")

    def _init(self) -> None:
        ...

    def _onParseModule(self, module: Module, source: CodeSource) -> None:
        ...

    def _onPreTransform(self) -> None:
        ...

    def _onPostTransform(self) -> None:
        ...
