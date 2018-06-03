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
        match = self.versions.get((major, minor, patch, pre, dev))
        if not match:
            return
        version_sort = operator.attrgetter('as_python.version')
        return next((c for c in sorted(match, key=version_sort, reverse=True)), None)

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
