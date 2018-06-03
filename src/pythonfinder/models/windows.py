# -*- coding=utf-8 -*-
import attr
import operator
from collections import defaultdict
from . import BaseFinder
from .path import VersionPath
from .python import PythonVersion
from ..utils import ensure_path


@attr.s
class WindowsFinder(BaseFinder):
    versions = attr.ib()

    @versions.default
    def get_versions(self):
        versions = defaultdict(VersionPath)
        from pythonfinder._vendor.pep514tools import environment as pep514env
        env_versions = pep514env.findall()
        path = None
        for version_object in env_versions:
            path = ensure_path(version_object.info.install_path.__getattr__(''))
            version = version_object.info.sys_version
            py_version = PythonVersion.from_windows_launcher(version_object)
            default_path = path / 'python.exe'
            if not default_path.exists():
                default_path = path / 'Scripts' / 'python.exe'
            exe_path = getattr(version_object.info.install_path, 'executable_path', default_path)
            path_entry_dict = {
                'path': path,
                'only_python': True,
                'pythons': {exe_path: py_version}
            }
            versions[py_version.version_tuple[:5]] = VersionPath.create(**path_entry_dict)
        return versions

    @classmethod
    def create(cls):
        return cls()
