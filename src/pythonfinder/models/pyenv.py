# -*- coding=utf-8 -*-
from __future__ import print_function, absolute_import
import attr
from collections import defaultdict
from . import BaseFinder
from .path import VersionPath
from .python import PythonVersion, VersionMap
from ..utils import optional_instance_of, ensure_path


try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


@attr.s
class PyenvFinder(BaseFinder):
    root = attr.ib(default=None, validator=optional_instance_of(Path))
    pyenv_versions = attr.ib()
    versions = attr.ib(default=attr.Factory(VersionMap))
    pythons = attr.ib()

    @pyenv_versions.default
    def get_versions(self):
        versions = defaultdict(VersionPath)
        for p in self.root.glob("versions/*"):
            version = PythonVersion.parse(p.name)
            version_tuple = (
                version.get("major"),
                version.get("minor"),
                version.get("patch"),
                version.get("is_prerelease"),
                version.get("is_devrelease"),
            )
            versions[version_tuple] = VersionPath.create(path=p.resolve(), only_python=True)
        return versions

    @pythons.default
    def get_pythons(self):
        pythons = defaultdict()
        for version_tuple, v in self.pyenv_versions.items():
            for p in v.paths.values():
                _path = ensure_path(p.path)
                if p.is_python:
                    pythons[_path.as_posix()] = p
                    self.versions.add_entry(p)
        return pythons

    @classmethod
    def create(cls, root):
        root = ensure_path(root)
        return cls(root=root)
