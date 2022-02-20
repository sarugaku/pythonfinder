from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Type

from pythonfinder.providers.base import BaseProvider, T
from pythonfinder.python import PythonVersion


@dataclass
class PathProvider(BaseProvider):
    """A provider that finds Python from PATH env."""

    paths: list[Path]

    @classmethod
    def create(cls: Type[T]) -> T | None:
        paths = [Path(path) for path in os.getenv("PATH", "").split(os.pathsep)]
        return cls(paths)

    def find_pythons(self) -> Iterable[PythonVersion]:
        for path in self.paths:
            yield from self.find_pythons_from_path(path)
