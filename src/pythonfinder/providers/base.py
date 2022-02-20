from __future__ import annotations

import abc
import logging
from pathlib import Path
from typing import Iterable, Type, TypeVar

from pythonfinder.python import PythonVersion
from pythonfinder.utils import path_is_python, path_is_readable

T = TypeVar("T", bound="BaseProvider")
logger = logging.getLogger("pythonfinder")


class BaseProvider(metaclass=abc.ABCMeta):
    """The base class for python providers"""

    @abc.abstractclassmethod
    def create(cls: Type[T]) -> T | None:
        """Return an instance of the provider or None if it is not available"""
        pass

    @abc.abstractmethod
    def find_pythons(self) -> Iterable[PythonVersion]:
        """Return the python versions found by the provider"""
        pass

    @staticmethod
    def find_pythons_from_path(path: Path) -> Iterable[PythonVersion]:
        """A general helper method to return pythons under a given path."""
        if not path.is_dir() or not path_is_readable(path):
            logger.debug("Invalid path or unreadable: %s", path)
            return iter([])
        python_versions = (
            PythonVersion(child.absolute())
            for child in path.iterdir()
            if path_is_python(child)
        )
        return filter(lambda p: p.is_valid(), python_versions)
