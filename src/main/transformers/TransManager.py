from __future__ import annotations

import ast
from ast import Module
from typing import Type, TextIO, TYPE_CHECKING

import Const
from log.Logger import Logger
from parsers.Source import Source
from transformers.OptimizeLevel import OptimizeLevel
from transformers.impl.ConstantFolding import ConstantFolding
from transformers.impl.DeadCodeElimination import DeadCodeElimination
from transformers.impl.DocumentRemover import DocumentRemover
from transformers.impl.LoopUnfolding import LoopUnfolding
from transformers.impl.UnusedVariableRemover import UnusedVariableRemover

if TYPE_CHECKING:
    from Pylang import Pylang
    from transformers.ITransformer import ITransformer


class TransManager:
    def __init__(self, pylang: Pylang, logger: Logger, level: OptimizeLevel):
        Const.transManager = self
        self.pylang = pylang
        self.logger = logger
        self.level = level
        self.sources: list[Source] = []
        """Raw sources from file. key: filename, value: Source object."""
        self.modules: dict[Source, Module] = {}
        self.transformers: dict[Type[ITransformer], ITransformer] = {}

    def register(self):
        def doRegister(transformer: ITransformer):
            self.transformers[type(transformer)] = transformer
            transformer.onRegister()

        doRegister(ConstantFolding())
        doRegister(DeadCodeElimination())
        doRegister(LoopUnfolding())
        doRegister(DocumentRemover())
        doRegister(UnusedVariableRemover())

    def parse(self, file: TextIO):
        try:
            source = Source(file.name[1::], file.read())
            assert source not in self.sources, "Parse twice is not allowed."
            module = ast.parse(source.getSources())
            self.logger.debug(f"Find module in source {file.name} with {len(module.body)} ast objects.")
            self.modules[source] = module
            self.sources.append(source)

            for transformer in self.transformers.values():
                transformer.onParseModule(module, source)
        except Exception as e:
            self.logger.warn(f"Failed to parse {file.name}. ignored.")
            self.logger.debug(str(e))

    def transform(self) -> list[Source]:
        cycle = 0
        isFinish = False
        while not isFinish:
            cycle += 1
            isFinish = True

            for source, module in self.modules.items():
                for transformer in self.transformers.values():
                    if not transformer.checkLevel():
                        continue

                    transformer.onPreTransform()
                    module = transformer.visit(module)
                    transformer.onPostTransform()

                    # Make sure there's nothing to optimize
                    if transformer.isChanged():
                        isFinish = False
                    ast.fix_missing_locations(module)
                self.modules[source] = module
            self.logger.info(f"Transforming cycle: {cycle}")
        self.logger.info("Transform done!")

        result: list[Source] = []
        for source, module in self.modules.items():
            result.append(Source(source.getFilename(), ast.unparse(module)))

        return result
