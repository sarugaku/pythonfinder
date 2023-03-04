from __future__ import annotations

import operator
from collections import defaultdict
from typing import Any, DefaultDict, TypeVar

import attr

from ..exceptions import InvalidPythonVersion
from ..utils import ensure_path
from .mixins import BaseFinder
from .path import PathEntry
from .python import PythonVersion

FinderType = TypeVar("FinderType")


@attr.s
class WindowsFinder(BaseFinder):
    paths = attr.ib(default=attr.Factory(list), type=list)
    version_list = attr.ib(default=attr.Factory(list), type=list)
    _versions: DefaultDict[tuple, PathEntry] = attr.ib()
    _pythons: DefaultDict[str, PathEntry] = attr.ib()

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
        version_matcher = operator.methodcaller(
            "matches", major, minor, patch, pre, dev, arch, python_name=name
        )
        pythons = [py for py in self.version_list if version_matcher(py)]
        version_sort = operator.attrgetter("version_sort")
        return [
            c.comes_from
            for c in sorted(pythons, key=version_sort, reverse=True)
            if c.comes_from
        ]

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
        return next(
            iter(
                v
                for v in self.find_all_python_versions(
                    major=major,
                    minor=minor,
                    patch=patch,
                    pre=pre,
                    dev=dev,
                    arch=arch,
                    name=name,
                )
            ),
            None,
        )

    @_versions.default
    def get_versions(self) -> DefaultDict[tuple, PathEntry]:
        versions: DefaultDict[tuple, PathEntry] = defaultdict(PathEntry)
        from pythonfinder._vendor.pep514tools import environment as pep514env

        env_versions = pep514env.findall()
        path = None
        for version_object in env_versions:
            install_path = getattr(version_object.info, "install_path", None)
            name = getattr(version_object, "tag", None)
            company = getattr(version_object, "company", None)
            if install_path is None:
                continue
            try:
                path = ensure_path(install_path.__getattr__(""))
            except AttributeError:
                continue
            if not path.exists():
                continue
            try:
                py_version = PythonVersion.from_windows_launcher(
                    version_object, name=name, company=company
                )
            except (InvalidPythonVersion, AttributeError):
                continue
            if py_version is None:
                continue
            self.version_list.append(py_version)
            python_path = (
                py_version.comes_from.path
                if py_version.comes_from
                else py_version.executable
            )
            python_kwargs = {python_path: py_version} if python_path is not None else {}
            base_dir = PathEntry.create(
                path, is_root=True, only_python=True, pythons=python_kwargs
            )
            versions[py_version.version_tuple[:5]] = base_dir
            self.paths.append(base_dir)
        return versions

    @property
    def versions(self) -> DefaultDict[tuple, PathEntry]:
        if not self._versions:
            self._versions = self.get_versions()
        return self._versions

    @_pythons.default
    def get_pythons(self) -> DefaultDict[str, PathEntry]:
        pythons: DefaultDict[str, PathEntry] = defaultdict()
        for version in self.version_list:
            _path = ensure_path(version.comes_from.path)
            pythons[_path.as_posix()] = version.comes_from
        return pythons

    @property
    def pythons(self) -> DefaultDict[str, PathEntry]:
        return self._pythons

    @pythons.setter
    def pythons(self, value: DefaultDict[str, PathEntry]) -> None:
        self._pythons = value

    @classmethod
    def create(cls: type[FinderType], *args: Any, **kwargs: Any) -> FinderType:
        return cls()
