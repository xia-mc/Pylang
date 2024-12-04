import ast
from ast import Constant, Call, Assign, Module

from pyfastutil.objects import ObjectArrayList
from pylang_annotations import native

import Const
from transformers.ITransformer import ITransformer
from transformers.OptimizeLevel import OptimizeLevel
from utils.eval.RangeUtils import RangeUtils


@native
class LoopUnfolding(ITransformer):
    def __init__(self):
        super().__init__("LoopUnfolding", OptimizeLevel.O2)
        self.variableMapping: dict[str, Constant] = {}
        self.working = False

    def visit_For(self, node):
        if RangeUtils.isRangeLoop(node):
            assert isinstance(node.iter, Call)

            evalRange = RangeUtils.evaluateRange(node.iter)
            if evalRange is None:
                return node

            start, end, step = evalRange

            if step == 0:
                # it will result a value error in runtime

                # why pycharm flags this as 'wrong type'
                self.flag("ValueError: range() arg 3 must not be zero.", node.iter)
                return self.generic_visit(node)
            if ((end - start) // step) * len(node.body) > Const.LOOP_UNFOLDING_MAX_LINES:
                return self.generic_visit(node)

            body = ObjectArrayList()

            for i in range(start, end, step):
                targetAssign = Assign(targets=[node.target], value=Constant(value=i))
                body.append(targetAssign)
                body.extend(node.body)

            self.done()
            return ast.copy_location(Module(body=body.to_list(), type_ignores=[]), node)

        return self.generic_visit(node)

    # TODO IDK why this doesn't work
    # def visit_ListComp(self, node):
    #     newGenerators = []
    #     body = [node.elt]
    #
    #     self.variableMapping.clear()
    #     for generator in node.generators:
    #         if not RangeUtils.isRangeLoop(generator):
    #             newGenerators.append(generator)
    #             continue
    #
    #         if not isinstance(generator.target, Name):
    #             newGenerators.append(generator)
    #             continue
    #
    #         assert isinstance(generator.iter, ast.Call)
    #
    #         evalRange = RangeUtils.evaluateRange(generator.iter)
    #         if evalRange is None:
    #             newGenerators.append(generator)
    #             continue
    #
    #         start, end, step = evalRange
    #
    #         # example: for i in range(100) for j in range(100)
    #         # then the elements count is 100 * 100
    #         if (end - start) / step * len(body) > Const.LOOP_UNFOLDING_MAX_LINES:
    #             self.variableMapping.clear()
    #             return node
    #
    #         newBody = []
    #         for i in range(start, end, step):
    #             self.variableMapping[generator.target.id] = Constant(value=i)
    #
    #             newElt = copy.deepcopy(node.elt)
    #             # wtf?
    #             self.working = True
    #             self.generic_visit(newElt)
    #             self.working = False
    #             newBody.append(newElt)
    #
    #         body = newBody
    #
    #     if not newGenerators:
    #         newElt = List(elts=body, ctx=ast.Load())
    #         return ast.copy_location(newElt, node)
    #     else:
    #         return node
    #
    # def visit_Name(self, node):
    #     if not isinstance(node.ctx, Load):
    #         return self.generic_visit(node)
    #     if not self.working:
    #         return self.generic_visit(node)
    #     if node.id not in self.variableMapping:
    #         return self.generic_visit(node)
    #     return self.variableMapping[node.id]
