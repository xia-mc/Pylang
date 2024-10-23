import os
import subprocess
from pathlib import Path
from typing import Sequence, Optional

import Const
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

    def compile(self, source: CodeSource) -> Optional[NativeSource]:
        # prepare datas
        cacheFolder = Path("cache", str(Path(source.getFilepath()).parent).replace(r"\\", "."))
        realName = "_" + source.getFilename().replace(".py", "")
        pyxPath = Path(cacheFolder, f"{realName}.pyx")
        setupPath = Path(cacheFolder, f"{realName}_setup.py")

        os.makedirs(cacheFolder, exist_ok=True)
        source.writeToFile(pyxPath)
        with open(setupPath, "w") as f:
            f.write(CythonCompiler.CYTHON_SETUP
                    .replace("%modules", str([str(pyxPath)]))
                    .replace("%compiler", self.compilerPath)
                    )

        # do compile
        cmd = f"python '{setupPath}' build_ext --build-lib='{cacheFolder}'"
        Const.logger.debug("Compile with command: ", cmd)
        subprocess.run(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # find compiled file
        for compiledPath in Path(cacheFolder).iterdir():
            if not compiledPath.name.startswith(realName):
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
                        source.getFilepath().replace(source.getFilename(), f"{realName}_native.{ext}"),
                        compiledRes
                    )
            except IOError:
                pass

        return None
