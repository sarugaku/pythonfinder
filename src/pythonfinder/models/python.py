# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function

import copy
import logging
import operator
import platform
import sys

from collections import defaultdict

import attr

from packaging.version import LegacyVersion, Version
from packaging.version import parse as parse_version

from vistir.compat import Path

from ..environment import ASDF_DATA_DIR, MYPY_RUNNING, PYENV_ROOT, SYSTEM_ARCH
from ..exceptions import InvalidPythonVersion
from ..utils import (
    _filter_none, ensure_path, get_python_version, is_in_path,
    optional_instance_of, parse_asdf_version_order, parse_pyenv_version_order,
    parse_python_version, unnest
)
from .mixins import BaseFinder, BasePath


if MYPY_RUNNING:
    from packaging.version import Version
    from typing import (
        DefaultDict, Optional, Callable, Generator, Any, Union, Tuple, List, Dict
    )
    from .path import PathEntry
    from .._vendor.pep514tools.environment import Environment


logger = logging.getLogger(__name__)


@attr.s(slots=True)
class PythonFinder(BaseFinder, BasePath):
    root = attr.ib(default=None, validator=optional_instance_of(Path), type=Path)
    # should come before versions, because its value is used in versions's default initializer.
    #: Whether to ignore any paths which raise exceptions and are not actually python
    ignore_unsupported = attr.ib(default=True, type=bool)
    #: The function to use to sort version order when returning an ordered verion set
    sort_function = attr.ib(default=None)  # type: Callable
    #: List of paths discovered during search
    paths = attr.ib(default=attr.Factory(list), type=list)
    #: The root locations used for discovery
    roots = attr.ib(default=attr.Factory(defaultdict), type=defaultdict)
    #: Glob path for python versions off of the root directory
    version_glob_path = attr.ib(default="versions/*", type=str)
    #: Versions discovered in the specified paths
    versions = attr.ib(type=dict)
    #: Corresponding python instances located
    pythons = attr.ib()  # type: DefaultDict[str, PathEntry]

    @property
    def expanded_paths(self):
        # type: () -> Generator
        return (
            path for path in unnest(p for p in self.versions.values())
            if path is not None
        )

    @property
    def is_pyenv(self):
        # type: () -> bool
        return is_in_path(str(self.root), PYENV_ROOT)

    @property
    def is_asdf(self):
        # type: () -> bool
        return is_in_path(str(self.root), ASDF_DATA_DIR)

    def get_version_order(self):
        # type: () -> List[Path]
        version_paths = [
            p for p in self.root.glob(self.version_glob_path)
            if not (p.parent.name == "envs" or p.name == "envs")
        ]
        versions = {v.name: v for v in version_paths}
        if self.is_pyenv:
            version_order = [versions[v] for v in parse_pyenv_version_order() if v in versions]
        elif self.is_asdf:
            version_order = [versions[v] for v in parse_asdf_version_order() if v in versions]
        for version in version_order:
            version_paths.remove(version)
        if version_order:
            version_order += version_paths
        else:
            version_order = version_paths
        return version_order

    @classmethod
    def version_from_bin_dir(cls, base_dir, name=None):
        # type: (Path, Optional[str]) -> PathEntry
        from .path import PathEntry
        py_version = None
        version_path = PathEntry.create(
            path=base_dir.absolute().as_posix(),
            only_python=True,
            name=base_dir.parent.name,
        )
        py_version = next(iter(version_path.find_all_python_versions()), None)
        return py_version

    @versions.default
    def get_versions(self):
        # type: () -> DefaultDict[Tuple, PathEntry]
        from .path import PathEntry
        versions = defaultdict()  # type: DefaultDict[Tuple, PathEntry]
        bin_ = "{base}/bin"
        for p in self.get_version_order():
            bin_dir = Path(bin_.format(base=p.as_posix()))
            version_path = None
            if bin_dir.exists():
                version_path = PathEntry.create(
                    path=bin_dir.absolute().as_posix(),
                    only_python=False,
                    name=p.name,
                    is_root=True,
                )
            version = None
            try:
                version = PythonVersion.parse(p.name)
            except (ValueError, InvalidPythonVersion):
                if version_path is not None:
                    entry = next(iter(version_path.find_all_python_versions()), None)
                if entry is None:
                    if self.ignore_unsupported:
                        continue
                    raise
                else:
                    version = entry.py_version.as_dict()
            except Exception:
                if not self.ignore_unsupported:
                    raise
                logger.warning(
                    "Unsupported Python version %r, ignoring...", p.name, exc_info=True
                )
                continue
            if not version:
                continue
            version_tuple = (
                version.get("major"),
                version.get("minor"),
                version.get("patch"),
                version.get("is_prerelease"),
                version.get("is_devrelease"),
                version.get("is_debug"),
            )
            self.roots[p] = version_path
            versions[version_tuple] = version_path
            self.paths.append(version_path)
        return versions

    @pythons.default
    def get_pythons(self):
        # type: () -> DefaultDict[str, List[PathEntry]]
        pythons = defaultdict()  # type: DefaultDict[str, List[PathEntry]]
        for p in self.paths:
            pythons.update(p.pythons)
        return pythons

    @classmethod
    def create(cls, root, sort_function, version_glob_path=None, ignore_unsupported=True):
        # type: (str, Callable, Optional[str], bool) -> PythonFinder
        root = ensure_path(root)
        if not version_glob_path:
            version_glob_path = "versions/*"
        return cls(root=root, ignore_unsupported=ignore_unsupported,
                   sort_function=sort_function, version_glob_path=version_glob_path)

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

        version_matcher = operator.methodcaller(
            "matches", major, minor, patch, pre, dev, arch, name
        )
        py = operator.attrgetter("as_python")
        pythons = (
            py_ver for py_ver in (py(p) for p in self.pythons.values() if p is not None)
            if py_ver is not None
        )
        # pythons = filter(None, [p.as_python for p in self.pythons.values()])
        matching_versions = filter(lambda py: version_matcher(py), pythons)
        version_sort = operator.attrgetter("version_sort")
        return sorted(matching_versions, key=version_sort, reverse=True)

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
        pythons = filter(None, [p.as_python for p in self.pythons.values()])
        matching_versions = filter(lambda py: version_matcher(py), pythons)
        version_sort = operator.attrgetter("version_sort")
        return next(iter(c for c in sorted(matching_versions, key=version_sort, reverse=True)), None)


@attr.s(slots=True)
class PythonVersion(object):
    major = attr.ib(default=0, type=int)
    minor = attr.ib(default=None)  # type: Optional[int]
    patch = attr.ib(default=0)  # type: Optional[int]
    is_prerelease = attr.ib(default=False, type=bool)
    is_postrelease = attr.ib(default=False, type=bool)
    is_devrelease = attr.ib(default=False, type=bool)
    is_debug = attr.ib(default=False, type=bool)
    version = attr.ib(default=None)  # type: Version
    architecture = attr.ib(default=None)  # type: Optional[str]
    comes_from = attr.ib(default=None)  # type: Optional[PathEntry]
    executable = attr.ib(default=None)  # type: Optional[str]
    name = attr.ib(default=None, type=str)

    @property
    def version_sort(self):
        # type: () -> Tuple[Optional[int], Optional[int], int, int]
        """version_sort tuple for sorting against other instances of the same class.

        Returns a tuple of the python version but includes a point for non-dev,
        and a point for non-prerelease versions.  So released versions will have 2 points
        for this value.  E.g. `(3, 6, 6, 2)` is a release, `(3, 6, 6, 1)` is a prerelease,
        `(3, 6, 6, 0)` is a dev release, and `(3, 6, 6, 3)` is a postrelease.
        """
        release_sort = 2
        if self.is_postrelease:
            release_sort = 3
        elif self.is_prerelease:
            release_sort = 1
        elif self.is_devrelease:
            release_sort = 0
        elif self.is_debug:
            release_sort = 1
        return (self.major, self.minor, self.patch if self.patch else 0, release_sort)

    @property
    def version_tuple(self):
        # type: () -> Tuple[int, Optional[int], Optional[int], bool, bool, bool]
        """Provides a version tuple for using as a dictionary key.

        :return: A tuple describing the python version meetadata contained.
        :rtype: tuple
        """

        return (
            self.major,
            self.minor,
            self.patch,
            self.is_prerelease,
            self.is_devrelease,
            self.is_debug,
        )

    def matches(
        self,
        major=None,  # type: Optional[int]
        minor=None,  # type: Optional[int]
        patch=None,  # type: Optional[int]
        pre=False,  # type: bool
        dev=False,  # type: bool
        arch=None,  # type: Optional[str]
        debug=False,  # type: bool
        name=None,  # type: Optional[str]
    ):
        # type: (...) -> bool
        result = False
        if arch:
            own_arch = self.get_architecture()
            if arch.isdigit():
                arch = "{0}bit".format(arch)
        if (
            (major is None or self.major and self.major == major)
            and (minor is None or self.minor and self.minor == minor)
            and (patch is None or self.patch and self.patch == patch)
            and (pre is None or self.is_prerelease == pre)
            and (dev is None or self.is_devrelease == dev)
            and (arch is None or own_arch == arch)
            and (debug is None or self.is_debug == debug)
            and (
                name is None
                or (name and self.name)
                and (self.name == name or self.name.startswith(name))
            )
        ):
            result = True
        return result

    def as_major(self):
        # type: () -> PythonVersion
        self_dict = attr.asdict(self, recurse=False, filter=_filter_none).copy()
        self_dict.update({"minor": None, "patch": None})
        return self.create(**self_dict)

    def as_minor(self):
        # type: () -> PythonVersion
        self_dict = attr.asdict(self, recurse=False, filter=_filter_none).copy()
        self_dict.update({"patch": None})
        return self.create(**self_dict)

    def as_dict(self):
        # type: () -> Dict[str, Union[int, bool, Version, None]]
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "is_prerelease": self.is_prerelease,
            "is_postrelease": self.is_postrelease,
            "is_devrelease": self.is_devrelease,
            "is_debug": self.is_debug,
            "version": self.version,
        }

    @classmethod
    def parse(cls, version):
        # type: (str) -> Dict[str, Union[str, int, Version]]
        """Parse a valid version string into a dictionary

        Raises:
            ValueError -- Unable to parse version string
            ValueError -- Not a valid python version

        :param version: A valid version string
        :type version: str
        :return: A dictionary with metadata about the specified python version.
        :rtype: dict.
        """

        version_dict = parse_python_version(str(version))
        if not version_dict:
            raise ValueError("Not a valid python version: %r" % version)
        return version_dict

    def get_architecture(self):
        # type: () -> str
        if self.architecture:
            return self.architecture
        arch = None
        if self.comes_from is not None:
            arch, _ = platform.architecture(self.comes_from.path.as_posix())
        elif self.executable is not None:
            arch, _ = platform.architecture(self.executable)
        if arch is None:
            arch, _ = platform.architecture(sys.executable)
        self.architecture = arch
        return self.architecture

    @classmethod
    def from_path(cls, path, name=None, ignore_unsupported=True):
        # type: (str, Optional[str], bool) -> PythonVersion
        """Parses a python version from a system path.

        Raises:
            ValueError -- Not a valid python path

        :param path: A string or :class:`~pythonfinder.models.path.PathEntry`
        :type path: str or :class:`~pythonfinder.models.path.PathEntry` instance
        :param str name: Name of the python distribution in question
        :param bool ignore_unsupported: Whether to ignore or error on unsupported paths.
        :return: An instance of a PythonVersion.
        :rtype: :class:`~pythonfinder.models.python.PythonVersion`
        """

        from .path import PathEntry

        if not isinstance(path, PathEntry):
            path = PathEntry.create(path, is_root=False, only_python=True, name=name)
        from ..environment import IGNORE_UNSUPPORTED
        ignore_unsupported = ignore_unsupported or IGNORE_UNSUPPORTED
        if not path.is_python:
            if not (ignore_unsupported or IGNORE_UNSUPPORTED):
                raise ValueError("Not a valid python path: %s" % path.path)
        py_version = get_python_version(path.path.absolute().as_posix())
        instance_dict = cls.parse(py_version.strip())
        if not isinstance(instance_dict.get("version"), Version) and not ignore_unsupported:
            raise ValueError("Not a valid python path: %s" % path)
        if not name:
            name = path.name
        instance_dict.update(
            {"comes_from": path, "name": name, "executable": path.as_posix()}
        )
        return cls(**instance_dict)  # type: ignore

    @classmethod
    def from_windows_launcher(cls, launcher_entry, name=None):
        # type: (Environment, Optional[str]) -> PythonVersion
        """Create a new PythonVersion instance from a Windows Launcher Entry

        :param launcher_entry: A python launcher environment object.
        :return: An instance of a PythonVersion.
        :rtype: :class:`~pythonfinder.models.python.PythonVersion`
        """

        from .path import PathEntry

        creation_dict = cls.parse(launcher_entry.info.version)
        base_path = ensure_path(launcher_entry.info.install_path.__getattr__(""))
        default_path = base_path / "python.exe"
        if not default_path.exists():
            default_path = base_path / "Scripts" / "python.exe"
        exe_path = ensure_path(
            getattr(launcher_entry.info.install_path, "executable_path", default_path)
        )
        creation_dict.update(
            {
                "architecture": getattr(
                    launcher_entry.info, "sys_architecture", SYSTEM_ARCH
                ),
                "executable": exe_path,
                "name": name
            }
        )
        py_version = cls.create(**creation_dict)
        comes_from = PathEntry.create(exe_path, only_python=True, name=name)
        comes_from.py_version = copy.deepcopy(py_version)
        py_version.comes_from = comes_from
        py_version.name = comes_from.name
        return py_version

    @classmethod
    def create(cls, **kwargs):
        # type: (...) -> PythonVersion
        if "architecture" in kwargs:
            if kwargs["architecture"].isdigit():
                kwargs["architecture"] = "{0}bit".format(kwargs["architecture"])
        return cls(**kwargs)


@attr.s
class VersionMap(object):
    versions = attr.ib(factory=defaultdict)  # type: DefaultDict[Tuple[int, Optional[int], Optional[int], bool, bool, bool], List[PathEntry]]

    def add_entry(self, entry):
        # type: (...) -> None
        version = entry.as_python  # type: PythonVersion
        if version:
            entries = self.versions[version.version_tuple]
            paths = {p.path for p in self.versions.get(version.version_tuple, [])}
            if entry.path not in paths:
                self.versions[version.version_tuple].append(entry)

    def merge(self, target):
        # type: (...) -> None
        for version, entries in target.versions.items():
            if version not in self.versions:
                self.versions[version] = entries
            else:
                current_entries = {
                    getattr(p, "path", p.executable) for p in
                    self.versions.get(version)  # type: ignore
                }
                new_entries = {p.path for p in entries}
                new_entries -= current_entries
                self.versions[version].append(
                    [e for e in entries if e.path in new_entries]
                )
