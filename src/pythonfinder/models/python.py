# -*- coding=utf-8 -*-
import attr
import platform
from fnmatch import fnmatch
from packaging.version import parse as parse_version, Version
from ..environment import SYSTEM_ARCH
from ..utils import KNOWN_EXTS, PYTHON_IMPLEMENTATIONS, _filter_none, optional_instance_of, get_python_version


try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


@attr.s
class PythonVersion(object):
    major = attr.ib(default=0)
    minor = attr.ib(default=None)
    patch = attr.ib(default=None)
    is_prerelease = attr.ib(default=False)
    is_postrelease = attr.ib(default=False)
    is_devrelease = attr.ib(default=False)
    version = attr.ib(default=None, validator=optional_instance_of(Version))
    architecture = attr.ib(default=None)
    comes_from = attr.ib(default=None)

    @property
    def version_tuple(self):
        return (self.major, self.minor, self.patch, self.is_prerelease, self.is_devrelease)

    def matches(self, major, minor=None, patch=None, pre=False, dev=False):
        return (
            self.major == major and
            (minor is None or self.minor == minor) and
            (patch is None or self.patch == patch) and
            self.is_prerelease == pre and
            self.is_devrelease == dev
        )

    def as_major(self):
        self_dict = attr.asdict(self, recurse=False, filter=_filter_none).copy()
        self_dict.update({
            'minor': None,
            'patch': None,
        })
        return self.create(**self_dict)

    def as_minor(self):
        self_dict = attr.asdict(self, recurse=False, filter=_filter_none).copy()
        self_dict.update({
            'patch': None,
        })
        return self.create(**self_dict)

    @classmethod
    def parse(cls, version):
        try:
            version = parse_version(version)
        except TypeError:
            raise ValueError('Unable to parse version: %s' % version)    
        if not version or not version.release:
            raise ValueError('Not a valid python version: %r' % version)
            return
        if len(version.release) >= 3:
            major, minor, patch = version.release[:3]
        elif len(version.release) == 2:
            major, minor = version.release
            patch = None
        else:
            major = version.release[0]
            minor = None
            patch = None
        return {
            'major': major,
            'minor': minor,
            'patch': patch,
            'is_prerelease': version.is_prerelease,
            'is_postrelease': version.is_postrelease,
            'is_devrelease': version.is_devrelease,
            'version': version,
        }

    @classmethod
    def from_path(cls, path):
        from .path import PathEntry
        if not isinstance(path, PathEntry):
            path = PathEntry(path)
        if not path.is_python:
            raise ValueError('Not a valid python path: %s' % path.path)
            return
        py_version, _ = get_python_version(str(path.path))
        instance_dict = cls.parse(py_version)
        if not isinstance(instance_dict.get('version'), Version):
            raise ValueError('Not a valid python path: %s' % path.path)
            return
        architecture, _ = platform.architecture(str(path.path))
        instance_dict.update({'comes_from': path, 'architecture': architecture})
        return cls(**instance_dict)

    @classmethod
    def from_windows_launcher(cls, launcher_entry):
        creation_dict = cls.parse(launcher_entry.info.version)
        creation_dict.update({'architecture': getattr(launcher_entry, 'sys_architecture', SYSTEM_ARCH)})
        return cls.create(**creation_dict)

    @classmethod
    def create(cls, **kwargs):
        return cls(**kwargs)
