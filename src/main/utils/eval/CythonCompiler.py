import keyword
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence, Optional

import Cython.Build
from pylang_annotations import native
from setuptools import setup

import Const
from utils.source.CodeSource import CodeSource
from utils.source.NativeSource import NativeSource


@native
class SetupModule:
    def __init__(self, compiler: str, modules: list[str], argv: list[str]):
        self.modules = modules
        self.argv = argv
        os.environ["CC"] = compiler

    def compile(self) -> None:
        setup(
            ext_modules=Cython.Build.cythonize(self.modules),
            script_args=self.argv
        )


@native
class CythonCompiler:

    def __init__(self, compilerPath: str):
        if compilerPath == "cl":
            self.compilerPrefix: str = compilerPath + " /O2 /GL"
        elif compilerPath in ("gcc", "clang"):
            self.compilerPrefix: str = compilerPath + " -Ofast"
        self.generatedNames: set[str] = set()

    @staticmethod
    def checkCompiler() -> Optional[str]:
        def doCheck(cmd: Sequence[str]) -> Optional[str]:
            try:
                res = subprocess.run(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode == 0:
                    return cmd[0]
            except (FileNotFoundError, Exception):
                return None
            return None

        return doCheck(["cl"]) or doCheck(["clang", "--version"]) or doCheck(["gcc", "--version"])

    @staticmethod
    def isValidImportName(name: str) -> bool:
        if not name.isidentifier():
            return False
        if keyword.iskeyword(name):
            return False
        if name in sys.modules:  # Prevent conflicts with already loaded modules
            return False
        return True

    def _getNewName(self, original: str, existsName: set[str]) -> str:
        """
        Generate a new valid import name for the given original name.
        This is an internal method, so no docstring is strictly necessary.
        """
        name: str = original
        for i in range(1000):
            if i > 0:
                importName = f"Native_{name}_{i}"
            else:
                importName = f"Native_{name}"

            if (CythonCompiler.isValidImportName(importName)
                    and importName not in existsName and importName not in self.generatedNames):
                self.generatedNames.add(importName)
                return importName

        raise RuntimeError(f"Failed to generate a valid import name for '{original}'")

    def compile(self, source: CodeSource, existsName: set[str] = None) -> Optional[NativeSource]:
        # prepare datas
        cacheFolder = Path("cache", str(Path(source.getFilepath()).parent).replace(r"\\", "."))
        filename = source.getFilename()
        try:
            newName = self._getNewName(filename.removesuffix(".py"), set() if existsName is None else existsName)
        except RuntimeError:
            raise ValueError("Fail to generate native lib name.")

        pyxPath = Path(cacheFolder, f"{newName}.pyx")

        os.makedirs(cacheFolder, exist_ok=True)
        source.writeToFile(pyxPath)

        # do compile
        Const.logger.info(f"Compiling {source.getFilename()} as native module...")
        setupModule = SetupModule(
            self.compilerPrefix,
            [str(pyxPath)],
            ["build_ext", f"--build-lib={cacheFolder}"]
        )
        setupModule.compile()

        # find compiled file
        for compiledPath in Path(cacheFolder).iterdir():
            if not compiledPath.name.startswith(newName):
                continue

            ext: str
            if compiledPath.name.endswith(".pyd"):
                ext = "pyd"
            elif compiledPath.name.endswith(".so"):
                ext = "so"
            else:
                continue

            try:
                if compiledPath.exists():
                    compiledRes: bytes
                    with open(compiledPath, "rb") as f:
                        compiledRes = f.read()

                    return NativeSource(
                        source.getFilepath().replace(source.getFilename(), f"{newName}.{ext}"),
                        compiledRes
                    )
            except IOError:
                pass

        return None
