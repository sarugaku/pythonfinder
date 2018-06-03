# -*- coding=utf-8 -*-
import attr
import operator
from collections import defaultdict
from . import BaseFinder
from .path import VersionPath
from .python import PythonVersion


try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


@attr.s
class WindowsFinder(BaseFinder):
    versions = attr.ib()

    def find_python_version(self, major, minor=None, patch=None, pre=False, dev=False):
        if major:
            major = int(major)
        if minor:
            minor = int(minor)
        if patch:
            patch = int(patch)
        return super(WindowsFinder, self).find_python_version(major, minor=minor, patch=patch, pre=pre, dev=dev)

    @versions.default
    def get_versions(self):
        versions = defaultdict(list)
        from pythonfinder._vendor.pep514tools import environment as pep514env
        env_versions = pep514env.findall()
        path = None
        for version_object in env_versions:
            path = Path(version_object.info.install_path.__getattr__(''))
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
            versions[py_version.version_tuple].append(VersionPath.create(**path_entry_dict))
        return versions
