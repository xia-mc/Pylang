from numbers import Integral, Real, Complex
from typing import Sequence, MutableSequence, MutableSet, MutableMapping, TypeVar

from pyfastutil.objects import ObjectArrayList
from pylang_annotations import native


@native
class TypeUtils:
    VISUAL_MRO: dict[type, ObjectArrayList[type]] = {
        int: ObjectArrayList([int] + Integral.mro()),
        bool: ObjectArrayList([bool, int] + Integral.mro()),
        float: ObjectArrayList([float] + Real.mro()),
        complex: ObjectArrayList([complex] + Complex.mro()),
        list: ObjectArrayList([list] + MutableSequence.mro()),
        tuple: ObjectArrayList([tuple] + Sequence.mro()),
        set: ObjectArrayList([set] + MutableSet.mro()),
        dict: ObjectArrayList([dict] + MutableMapping.mro())
    }

    @staticmethod
    def getVisualMRO(cls: type) -> ObjectArrayList[type]:
        """
        Returns a virtual MRO for a given class. For special types like int, float, etc.,
        it returns an extended MRO that includes abstract base classes (e.g., Number).
        Otherwise, it returns the real MRO of the class.
        """
        if cls in TypeUtils.VISUAL_MRO:
            return TypeUtils.VISUAL_MRO[cls]

        return ObjectArrayList(cls.mro())

    @staticmethod
    def predictType(type1: type, *types: type) -> type:
        """
        Predicts the nearest common parent class (most specific) for the given types.
        """
        if len(types) == 0:
            return type1

        # Step 1: Get virtual MROs for all types
        allTypes = (type1,) + types
        mroList = ObjectArrayList(TypeUtils.getVisualMRO(t) for t in allTypes)

        # Step 2: Find valid MROs that contain all types
        validMro = ObjectArrayList()
        for mro in mroList:
            if all(cls in mro for cls in allTypes):
                # Calculate the maximum distance of the types in this MRO
                maxDist = max(mro.index(cls) for cls in allTypes)
                validMro.append((mro, maxDist))

        # Step 3: Return the nearest common parent class
        if not validMro:
            return object

        nearestMro, distance = min(validMro, key=lambda t: t[1])
        return nearestMro[distance]

    @staticmethod
    def checkMatchTypeVar(obj, typeVar: TypeVar) -> bool:
        """
        判断对象是否符合 TypeVar 的约束。
        """
        if typeVar.__constraints__:
            return isinstance(obj, typeVar.__constraints__)
        if typeVar.__bound__:
            return isinstance(obj, typeVar.__bound__)
        return True
