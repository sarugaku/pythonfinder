# -*- coding=utf-8 -*-
from __future__ import absolute_import, unicode_literals

import abc
import attr
import operator
import six

from cached_property import cached_property
from collections import defaultdict

from vistir.compat import Path, fs_str

from ..utils import ensure_path, KNOWN_EXTS, unnest, path_is_known_executable, looks_like_python
from ..environment import MYPY_RUNNING
from ..exceptions import InvalidPythonVersion

if MYPY_RUNNING:
    from .path import PathEntry
    from .python import PythonVersion
    from typing import Optional, Union, Any, Dict, List, DefaultDict, Generator, Tuple



@attr.s
class BasePath(object):
    path = attr.ib(default=None)  # type: Path
    _children = attr.ib(default=attr.Factory(dict))  # type: Dict[str, PathEntry]
    only_python = attr.ib(default=False)  # type: bool
    name = attr.ib(type=str)
    py_version = attr.ib()  # type: PythonVersion
    _pythons = attr.ib(default=attr.Factory(defaultdict))  # type: DefaultDict[str, PathEntry]

    def __str__(self):
        # type: () -> str
        return fs_str("{0}".format(self.path.as_posix()))

    def which(self, name):
        # type: (str) -> PathEntry
        """Search in this path for an executable.

        :param executable: The name of an executable to search for.
        :type executable: str
        :returns: :class:`~pythonfinder.models.PathEntry` instance.
        """

        valid_names = [name] + [
            "{0}.{1}".format(name, ext).lower() if ext else "{0}".format(name).lower()
            for ext in KNOWN_EXTS
        ]
        children = self.children
        found = next(
            (
                children[(self.path / child).as_posix()]
                for child in valid_names
                if (self.path / child).as_posix() in children
            ),
            None,
        )
        return found

    @property
    def children(self):
        # type: () -> Dict[str, PathEntry]
        return self._children

    @cached_property
    def as_python(self):
        # type: () -> PythonVersion
        py_version = None
        if self.py_version:
            return self.py_version
        if not self.is_dir and self.is_python:
            try:
                from .python import PythonVersion
                py_version = PythonVersion.from_path(path=attr.evolve(self), name=self.name)
            except (ValueError, InvalidPythonVersion):
                py_version = None
        return py_version

    @name.default
    def get_name(self):
        # type: () -> str
        return self.path.name

    @cached_property
    def is_dir(self):
        # type: () -> bool
        try:
            ret_val = self.path.is_dir()
        except OSError:
            ret_val = False
        return ret_val

    @cached_property
    def is_executable(self):
        # type: () -> bool
        return path_is_known_executable(self.path)

    @cached_property
    def is_python(self):
        # type: () -> bool
        return self.is_executable and (
            looks_like_python(self.path.name)
        )

    @py_version.default
    def get_py_version(self):
        # type: () -> PythonVersion
        from ..environment import IGNORE_UNSUPPORTED
        if self.is_dir:
            return None
        if self.is_python:
            py_version = None
            from .python import PythonVersion
            try:
                py_version = PythonVersion.from_path(path=self, name=self.name)
            except (InvalidPythonVersion, ValueError):
                py_version = None
            except Exception:
                if not IGNORE_UNSUPPORTED:
                    raise
            return py_version
        return

    @property
    def pythons(self):
        # type: () -> DefaultDict[str, PathEntry]
        if not self._pythons:
            if self.is_dir:
                for path, entry in self.children.items():
                    _path = ensure_path(entry.path)
                    if entry.is_python:
                        self._pythons[_path.as_posix()] = entry
            else:
                if self.is_python:
                    _path = ensure_path(self.path)
                    self._pythons[_path.as_posix()] = self
        return self._pythons

    def find_all_python_versions(
        self,
        major=None,  # type: Optional[Union[str, int]]
        minor=None,  # type: Optional[int]
        patch=None,  # type: Optional[int]
        pre=None,  # type: Optional[bool]
        dev=None,  # type: Optional[bool]
        arch=None,  # type: Optional[str]
        name=None,  # type: Optional[str]
    ):
        # type: (...) -> List[PathEntry]
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

        call_method = (
            "find_all_python_versions" if self.is_dir else "find_python_version"
        )
        sub_finder = operator.methodcaller(
            call_method, major, minor, patch, pre, dev, arch, name
        )
        if not self.is_dir:
            return sub_finder(self)
        path_filter = filter(None, (sub_finder(p) for p in self.children.values()))
        version_sort = operator.attrgetter("as_python.version_sort")
        return [c for c in sorted(path_filter, key=version_sort, reverse=True)]

    def find_python_version(
        self,
        major=None,  # type: Optional[Union[str, int]]
        minor=None,  # type: Optional[int]
        patch=None,  # type: Optional[int]
        pre=None,  # type: Optional[bool]
        dev=None,  # type: Optional[bool]
        arch=None,  # type: Optional[str]
        name=None,  # type: Optional[str]
    ):
        # type: (...) -> PathEntry
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
            "matches", major, minor, patch, pre, dev, arch, name
        )
        is_py = operator.attrgetter("is_python")
        py_version = operator.attrgetter("as_python")
        if not self.is_dir:
            if self.is_python and self.as_python and version_matcher(self.py_version):
                return attr.evolve(self)  # type: ignore
            return
        finder = (
            (child, child.as_python)
            for child in unnest(self.pythons.values())
            if child is not None and child.as_python is not None
        )
        py_filter = (
            [entry, py_version.version_sort] for entry, py_version in finder
            if (py_version is not None and version_matcher(py_version))
        )
        return next(iter(
            entry for entry in
            sorted(py_filter, key=operator.itemgetter(1), reverse=True)), None
        )


@six.add_metaclass(abc.ABCMeta)
class BaseFinder(object):
    def __init__(self):
        self.pythons = defaultdict(list)  # type: DefaultDict[str, List[PathEntry]]
        self.versions = defaultdict(list)  # type: Dict[Tuple, PathEntry]

    def get_versions(self):
        # type: () -> None
        """Return the available versions from the finder"""
        raise NotImplementedError

    @classmethod
    def create(cls):
        # type: () -> None
        raise NotImplementedError

    @property
    def version_paths(self):
        # type: () -> Any
        return self.versions.values()

    @property
    def expanded_paths(self):
        # type: () -> Any
        return (p.paths.values() for p in self.version_paths)
