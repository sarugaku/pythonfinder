# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function

import operator

from collections import defaultdict

import attr

from ..exceptions import InvalidPythonVersion
from ..utils import ensure_path
from .mixins import BaseFinder
from .path import PathEntry
from .python import PythonVersion, VersionMap
from ..environment import MYPY_RUNNING

if MYPY_RUNNING:
    from typing import DefaultDict, Tuple, List, Optional, Union


@attr.s
class WindowsFinder(BaseFinder):
    paths = attr.ib(default=attr.Factory(list), type=list)
    version_list = attr.ib(default=attr.Factory(list), type=list)
    versions = attr.ib()  # type: DefaultDict[Tuple, PathEntry]
    pythons = attr.ib()  # type: DefaultDict[str, List[PathEntry]]

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
        # type (...) -> List[PathEntry]
        version_matcher = operator.methodcaller(
            "matches", major, minor, patch, pre, dev, arch, name
        )
        py_filter = filter(
            None, filter(lambda c: version_matcher(c), self.version_list)
        )
        version_sort = operator.attrgetter("version_sort")
        return [c.comes_from for c in sorted(py_filter, key=version_sort, reverse=True)]

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
        return next(iter(v for v in self.find_all_python_versions(
            major=major,
            minor=minor,
            patch=patch,
            pre=pre,
            dev=dev,
            arch=arch,
            name=None,
            )), None
        )

    @versions.default
    def get_versions(self):
        # type: () -> DefaultDict[Tuple, PathEntry]
        versions = defaultdict(PathEntry)  # type: DefaultDict[Tuple, PathEntry]
        from pythonfinder._vendor.pep514tools import environment as pep514env

        env_versions = pep514env.findall()
        path = None
        for version_object in env_versions:
            install_path = getattr(version_object.info, "install_path", None)
            if install_path is None:
                continue
            try:
                path = ensure_path(install_path.__getattr__(""))
            except AttributeError:
                continue
            try:
                py_version = PythonVersion.from_windows_launcher(version_object)
            except InvalidPythonVersion:
                continue
            self.version_list.append(py_version)
            base_dir = PathEntry.create(
                path,
                is_root=True,
                only_python=True,
                pythons={py_version.comes_from.path: py_version},
            )
            versions[py_version.version_tuple[:5]] = base_dir
            self.paths.append(base_dir)
        return versions

    @pythons.default
    def get_pythons(self):
        # type: () -> DefaultDict[str, List[PathEntry]]
        pythons = defaultdict()  # type: DefaultDict[str, List[PathEntry]]
        for version in self.version_list:
            _path = ensure_path(version.comes_from.path)
            pythons[_path.as_posix()] = version.comes_from
        return pythons

    @classmethod
    def create(cls):
        # type: () -> WindowsFinder
        return cls()
