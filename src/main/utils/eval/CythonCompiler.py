import keyword
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence, Optional

import Const
from log.LogLevel import LogLevel
from utils.source.CodeSource import CodeSource
from utils.source.NativeSource import NativeSource


class CythonCompiler:
    CYTHON_SETUP = """import os
from setuptools import setup
from Cython.Build import cythonize

os.environ["CC"] = "%compiler"

setup(
    ext_modules=cythonize(%modules)
)
"""

    def __init__(self, compilerPath: str):
        self.compilerPath: str = compilerPath

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

    @staticmethod
    def _getNewName(original: str, existsName: set[str]) -> str:
        """
        Generate a new valid import name for the given original name.
        This is an internal method, so no docstring is strictly necessary.
        """
        name: str = original
        for i in range(1000):
            importName = name + "_native"

            if (CythonCompiler.isValidImportName(importName)
                    and importName not in existsName):
                return importName

            name = f"_{i}_{name}"

        raise RuntimeError(f"Failed to generate a valid import name for '{original}'")

    def compile(self, source: CodeSource, existsName: set[str] = None) -> Optional[NativeSource]:
        # prepare datas
        cacheFolder = Path("cache", str(Path(source.getFilepath()).parent).replace(r"\\", "."))
        filename = source.getFilename()
        try:
            newName = self._getNewName(filename.removesuffix(".py"), set() if existsName is None else existsName)
        except RuntimeError:
            return None
        pyxPath = Path(cacheFolder, f"{newName}.pyx")
        setupPath = Path(cacheFolder, f"{newName}_setup.py")

        os.makedirs(cacheFolder, exist_ok=True)
        source.writeToFile(pyxPath)
        with open(setupPath, "w") as f:
            f.write(CythonCompiler.CYTHON_SETUP
                    .replace("%modules", str([str(pyxPath)]))
                    .replace("%compiler", self.compilerPath)
                    )

        # do compile
        cmd = [
            sys.executable,
            str(setupPath),
            "build_ext",
            f"--build-lib={cacheFolder}"
        ]
        Const.logger.debug("Compile with command: ", " ".join(cmd))
        if Const.logger.level <= LogLevel.DEBUG:
            subprocess.run(
                cmd,  # Pass the command as a list
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            subprocess.run(
                cmd,  # Pass the command as a list
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

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
