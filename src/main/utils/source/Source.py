import os.path
from abc import ABC, abstractmethod
from os import PathLike
from typing import TypeVar

T = TypeVar("T", bound=int | str | bytes | PathLike[str] | PathLike[bytes])


class Source(ABC):
    @abstractmethod
    def getFilepath(self) -> T: ...

    def getFilename(self) -> str:
        return os.path.basename(self.getFilepath())

    @abstractmethod
    def writeToFile(self, path: T) -> None: ...
