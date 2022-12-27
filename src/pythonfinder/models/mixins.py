from __future__ import annotations

import abc
import operator
from collections import defaultdict
from typing import TYPE_CHECKING, Any, DefaultDict, Generator, Iterator, List, TypeVar

import attr

from ..compat import fs_str
from ..exceptions import InvalidPythonVersion
from ..utils import (
    KNOWN_EXTS,
    expand_paths,
    looks_like_python,
    path_is_known_executable,
)

if TYPE_CHECKING:
    from pathlib import Path

    from .path import PathEntry
    from .python import PythonVersion

    BaseFinderType = TypeVar("BaseFinderType")


@attr.s(slots=True)
class BasePath:
    path: Path = attr.ib(default=None)
    _children: dict[str, PathEntry] = attr.ib(default=attr.Factory(dict), order=False)
    only_python: bool = attr.ib(default=False)
    name = attr.ib(type=str)
    _py_version: PythonVersion | None = attr.ib(default=None, order=False)
    _pythons: DefaultDict[str, PathEntry] = attr.ib(
        default=attr.Factory(defaultdict), order=False
    )
    _is_dir: bool | None = attr.ib(default=None, order=False)
    _is_executable: bool | None = attr.ib(default=None, order=False)
    _is_python: bool | None = attr.ib(default=None, order=False)

    def __str__(self) -> str:
        return fs_str(f"{self.path.as_posix()}")

    def __lt__(self, other: BasePath) -> bool:
        return self.path.as_posix() < other.path.as_posix()

    def __lte__(self, other: BasePath) -> bool:
        return self.path.as_posix() <= other.path.as_posix()

    def __gt__(self, other: BasePath) -> bool:
        return self.path.as_posix() > other.path.as_posix()

    def __gte__(self, other: BasePath) -> bool:
        return self.path.as_posix() >= other.path.as_posix()

    def which(self, name: str) -> PathEntry | None:
        """Search in this path for an executable.

        :param executable: The name of an executable to search for.
        :type executable: str
        :returns: :class:`~pythonfinder.models.PathEntry` instance.
        """

        valid_names = [name] + [
            f"{name}.{ext}".lower() if ext else f"{name}".lower() for ext in KNOWN_EXTS
        ]
        children = self.children
        found = None
        if self.path is not None:
            found = next(
                (
                    children[(self.path / child).as_posix()]
                    for child in valid_names
                    if (self.path / child).as_posix() in children
                ),
                None,
            )
        return found

    def __del__(self):
        for key in ["_is_dir", "_is_python", "_is_executable", "_py_version"]:
            if getattr(self, key, None):
                try:
                    delattr(self, key)
                except Exception:
                    print(f"failed deleting key: {key}")
        self._children = {}
        for key in list(self._pythons.keys()):
            del self._pythons[key]
        self._pythons = None
        self._py_version = None
        self.path = None

    @property
    def children(self) -> dict[str, PathEntry]:
        if not self.is_dir:
            return {}
        return self._children

    @property
    def as_python(self) -> PythonVersion:
        py_version = None
        if self.py_version:
            return self.py_version
        if not self.is_dir and self.is_python:
            try:
                from .python import PythonVersion

                py_version = PythonVersion.from_path(  # type: ignore
                    path=self, name=self.name
                )
            except (ValueError, InvalidPythonVersion):
                pass
        if py_version is None:
            pass
        self.py_version = py_version
        return py_version  # type: ignore

    @name.default
    def get_name(self) -> str | None:
        if self.path:
            return self.path.name
        return None

    @property
    def is_dir(self) -> bool:
        if self._is_dir is None:
            if not self.path:
                ret_val = False
            try:
                ret_val = self.path.is_dir()
            except OSError:
                ret_val = False
            self._is_dir = ret_val
        return self._is_dir

    @is_dir.setter
    def is_dir(self, val: bool) -> None:
        self._is_dir = val

    @is_dir.deleter
    def is_dir(self) -> None:
        self._is_dir = None

    @property
    def is_executable(self) -> bool:
        if self._is_executable is None:
            if not self.path:
                self._is_executable = False
            else:
                self._is_executable = path_is_known_executable(self.path)
        return self._is_executable

    @is_executable.setter
    def is_executable(self, val: bool) -> None:
        self._is_executable = val

    @is_executable.deleter
    def is_executable(self) -> None:
        self._is_executable = None

    @property
    def is_python(self) -> bool:
        if self._is_python is None:
            if not self.path:
                self._is_python = False
            else:
                self._is_python = self.is_executable and (
                    looks_like_python(self.path.name)
                )
        return self._is_python

    @is_python.setter
    def is_python(self, val: bool) -> None:
        self._is_python = val

    @is_python.deleter
    def is_python(self) -> None:
        self._is_python = None

    def get_py_version(self) -> PythonVersion | None:
        from ..environment import IGNORE_UNSUPPORTED

        if self.is_dir:
            return None
        if self.is_python:
            py_version = None
            from .python import PythonVersion

            try:
                py_version = PythonVersion.from_path(  # type: ignore
                    path=self, name=self.name
                )
            except (InvalidPythonVersion, ValueError):
                py_version = None
            except Exception:
                if not IGNORE_UNSUPPORTED:
                    raise
            return py_version
        return None

    @property
    def py_version(self) -> PythonVersion | None:
        if not self._py_version:
            py_version = self.get_py_version()
            self._py_version = py_version
        else:
            py_version = self._py_version
        return py_version

    @py_version.setter
    def py_version(self, val: PythonVersion | None) -> None:
        self._py_version = val

    @py_version.deleter
    def py_version(self) -> None:
        self._py_version = None

    def _iter_pythons(self) -> Iterator:
        if self.is_dir:
            for entry in self.children.values():
                if entry is None:
                    continue
                elif entry.is_dir:
                    yield from entry._iter_pythons()
                elif entry.is_python and entry.as_python is not None:
                    yield entry
        elif self.is_python and self.as_python is not None:
            yield self  # type: ignore

    @property
    def pythons(self) -> DefaultDict[str | Path, PathEntry]:
        if not self._pythons:
            from .path import PathEntry

            self._pythons = defaultdict(PathEntry)
            for python in self._iter_pythons():
                python_path = python.path.as_posix()  # type: ignore
                self._pythons[python_path] = python
        return self._pythons

    def __iter__(self) -> Iterator:
        yield from self.children.values()

    def __next__(self) -> Generator:
        return next(iter(self))

    def next(self) -> Generator:
        return self.__next__()

    def find_all_python_versions(
        self,
        major: str | int | None = None,
        minor: int | None = None,
        patch: int | None = None,
        pre: bool | None = None,
        dev: bool | None = None,
        arch: str | None = None,
        name: str | None = None,
    ) -> list[PathEntry]:
        """Search for a specific python version on the path. Return all copies

        :param major: Major python version to search for.
        :type major: int
        :param int minor: Minor python version to search for, defaults to None
        :param int patch: Patch python version to search for, defaults to None
        :param bool pre: Search for prereleases (default None) - prioritize releases if None
        :param bool dev: Search for devreleases (default None) - prioritize releases if None
        :param str arch: Architecture to include, e.g. '64bit', defaults to None
        :param str name: The name of a python version, e.g. ``anaconda3-5.3.0``
        :return: A list of :class:`~pythonfinder.models.PathEntry` instances matching the version requested.
        :rtype: List[:class:`~pythonfinder.models.PathEntry`]
        """

        call_method = "find_all_python_versions" if self.is_dir else "find_python_version"
        sub_finder = operator.methodcaller(
            call_method, major, minor, patch, pre, dev, arch, name
        )
        if not self.is_dir:
            return sub_finder(self)
        unnested = [sub_finder(path) for path in expand_paths(self)]
        version_sort = operator.attrgetter("as_python.version_sort")
        unnested = [p for p in unnested if p is not None and p.as_python is not None]
        paths = sorted(unnested, key=version_sort, reverse=True)
        return list(paths)

    def find_python_version(
        self,
        major: str | int | None = None,
        minor: int | None = None,
        patch: int | None = None,
        pre: bool | None = None,
        dev: bool | None = None,
        arch: str | None = None,
        name: str | None = None,
    ) -> PathEntry | None:
        """Search or self for the specified Python version and return the first match.

        :param major: Major version number.
        :type major: int
        :param int minor: Minor python version to search for, defaults to None
        :param int patch: Patch python version to search for, defaults to None
        :param bool pre: Search for prereleases (default None) - prioritize releases if None
        :param bool dev: Search for devreleases (default None) - prioritize releases if None
        :param str arch: Architecture to include, e.g. '64bit', defaults to None
        :param str name: The name of a python version, e.g. ``anaconda3-5.3.0``
        :returns: A :class:`~pythonfinder.models.PathEntry` instance matching the version requested.
        """

        version_matcher = operator.methodcaller(
            "matches", major, minor, patch, pre, dev, arch, python_name=name
        )
        if not self.is_dir:
            if self.is_python and self.as_python and version_matcher(self.py_version):
                return self  # type: ignore

        matching_pythons = [
            [entry, entry.as_python.version_sort]
            for entry in self._iter_pythons()
            if (
                entry is not None
                and entry.as_python is not None
                and version_matcher(entry.py_version)
            )
        ]
        results = sorted(matching_pythons, key=operator.itemgetter(1, 0), reverse=True)
        return next(iter(r[0] for r in results if r is not None), None)


class BaseFinder(metaclass=abc.ABCMeta):
    def __init__(self):
        #: Maps executable paths to PathEntries
        from .path import PathEntry

        self._pythons: DefaultDict[str, PathEntry] = defaultdict(PathEntry)
        self._versions: dict[tuple, PathEntry] = defaultdict(PathEntry)

    def get_versions(self) -> DefaultDict[tuple, PathEntry]:
        """Return the available versions from the finder"""
        raise NotImplementedError

    @classmethod
    def create(cls, *args: Any, **kwargs: Any) -> BaseFinderType:
        raise NotImplementedError

    @property
    def version_paths(self) -> Any:
        return self._versions.values()

    @property
    def expanded_paths(self) -> Any:
        return (p.paths.values() for p in self.version_paths)

    @property
    def pythons(self) -> DefaultDict[str, PathEntry]:
        return self._pythons

    @pythons.setter
    def pythons(self, value: DefaultDict[str, PathEntry]) -> None:
        self._pythons = value
