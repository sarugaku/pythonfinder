from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Type

from pythonfinder.providers.base import BaseProvider, T
from pythonfinder.python import PythonVersion


class PyenvProvider(BaseProvider):
    """A provider that finds python installed with pyenv"""

    def __init__(self, root: Path) -> None:
        self.root = root

    @classmethod
    def create(cls: Type[T]) -> T | None:
        pyenv_root = os.path.expanduser(
            os.path.expandvars(os.getenv("PYENV_ROOT", "~/.pyenv"))
        )
        if not os.path.exists(pyenv_root):
            return None
        return cls(Path(pyenv_root))

    def find_pythons(self) -> Iterable[PythonVersion]:
        for version in self.root.joinpath("versions").iterdir():
            if version.is_dir():
                bindir = version / "bin"
                if not bindir.exists():
                    bindir = version / "Scripts"
                yield from self.find_pythons_from_path(bindir)
