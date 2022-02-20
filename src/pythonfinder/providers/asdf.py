from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Type

from pythonfinder.providers.base import BaseProvider, T
from pythonfinder.python import PythonVersion


class AsdfProvider(BaseProvider):
    """A provider that finds python installed with asdf"""

    def __init__(self, root: Path) -> None:
        self.root = root

    @classmethod
    def create(cls: Type[T]) -> T | None:
        asdf_root = os.path.expanduser(
            os.path.expandvars(os.getenv("ASDF_DATA_DIR", "~/.asdf"))
        )
        if not os.path.exists(asdf_root):
            return None
        return cls(Path(asdf_root))

    def find_pythons(self) -> Iterable[PythonVersion]:
        python_dir = self.root / "installs/python"
        if not python_dir.exists():
            return
        for version in python_dir.iterdir():
            if version.is_dir():
                bindir = version / "bin"
                if not bindir.exists():
                    bindir = version / "Scripts"
                yield from self.find_pythons_from_path(bindir)
