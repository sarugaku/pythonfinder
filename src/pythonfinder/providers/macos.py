from __future__ import annotations

from pathlib import Path
from typing import Iterable, Type

from pythonfinder.providers.base import BaseProvider, T
from pythonfinder.python import PythonVersion


class MacOSProvider(BaseProvider):
    """A provider that finds python from macos typical install base
    with python.org installer.
    """

    INSTALL_BASE = Path("/Library/Frameworks/Python.framework/Versions/")

    @classmethod
    def create(cls: Type[T]) -> T | None:
        if not cls.INSTALL_BASE.exists():
            return None
        return cls()

    def find_pythons(self) -> Iterable[PythonVersion]:
        for version in self.INSTALL_BASE.iterdir():
            if version.is_dir():
                yield from self.find_pythons_from_path(version / "bin")
