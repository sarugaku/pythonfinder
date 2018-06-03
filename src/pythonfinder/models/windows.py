# -*- coding=utf-8 -*-
import attr
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

    @versions.default
    def get_versions(self):
        versions = defaultdict(VersionPath)
        from pythonfinder._vendor.pep514tools import environment as pep514env
        versions = pep514env.findall()
        path = None
        for version_object in versions:
            path = Path(version_object.info.install_path.__getattr__(''))
            version = version_object.info.sys_version
            py_version = PythonVersion.from_windows_launcher(version_object)
            path_entry_dict = {
                'path': path,
                'only_python': True,
                'pythons': {version.info.install_path.executable_path: py_version}
            }
            versions[py_version.version_tuple] = VersionPath.create(**path_entry_dict)
        return versions
