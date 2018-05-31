# -*- coding=utf-8 -*-
import attr
import os
import subprocess
import sys
from collections import defaultdict
from packaging.version import parse as parse_version, Version

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

PYTHON_IMPLEMENTATIONS = (
    'python',
    'ironpython',
    'jython',
    'pypy',
)

KNOWN_EXTS = {'exe', 'py', 'fish', 'sh'}
KNOWN_EXTS = KNOWN_EXTS | set(filter(None, os.environ.get('PATHEXT', '').split(os.pathsep)))


def _run(arg_list):
    """Wrapper around `subprocess.check_output` with decoding for bytestrings."""
    result = subprocess.check_output(arg_list)
    if hasattr(result, 'decode'):
        result = result.decode()
    return result.strip()


def get_python_version(path):
    """Get python version string using subprocess from a given path."""
    version_cmd = [path, "-c", "import sys; print(sys.version.split()[0])"]
    return _run(version_cmd)


def optional_instance_of(cls):
    return attr.validators.optional(attr.validators.instance_of(cls))


def path_and_exists(path):
    return attr.validators.instance_of(Path) and path.exists()


def path_is_executable(path):
    return os.access(str(path), os.X_OK)


def path_is_known_executable(path):
    return path_is_executable(path) or os.access(str(path), os.R_OK) and path.suffix in KNOWN_EXTS


def _filter_none(k, v):
    if v:
        return True
    return False


@attr.s
class PathEntry(object):
    path = attr.ib(default=None, validator=optional_instance_of(Path))
    children = attr.ib(default=None)
    is_root = attr.ib(default=True)

    def __attrs_post_init__(self):
        if self.is_dir and self.is_root:
            self.children = {}
            for child in self.path.iterdir():
                self.children[child.as_posix()] = PathEntry(child, is_root=False)

    @classmethod
    def create(cls, path, is_root=False):
        return cls(path=Path(os.path.expandvars(str(path))), is_root=is_root)

    @property
    def name(self):
        return self.path.name

    @property
    def is_dir(self):
        return self.path.is_dir()

    @property
    def is_executable(self):
        return path_is_known_executable(self.path)

    @property
    def is_python(self):
        return (self.is_executable and any(self.path.name.lower().startswith(py_name) for py_name in PYTHON_IMPLEMENTATIONS) and not any(self.path.name.lower().endswith(bad_name) for bad_name in ['-config', '-build']))


@attr.s
class SystemPath(object):
    paths = attr.ib(default=attr.Factory(defaultdict))
    executables = attr.ib()
    python_executables = attr.ib()
    python_version_dict = attr.ib()

    @executables.default
    def get_executables(self):
        return [p for p in self.paths.values() if p.is_executable]

    @python_executables.default
    def get_python_executables(self):
        return [p for p in self.paths.values() if p.is_python]

    @python_version_dict.default
    def get_python_version_dict(self):
        version_dict = defaultdict(list)
        for p in self.python_executables:
            try:
                version_object = PythonVersion.from_path(p)
            except ValueError:
                continue
            version_dict[version_object.version_tuple].append(version_object)

    def __attrs_post_init__(self):
        pass

    @classmethod
    def create(cls, path=None, system=False):
        path_entries = defaultdict(PathEntry)
        paths = os.environ.get('PATH').split(os.pathsep)
        if path:
            paths = [path,] + paths
        if sys:
            paths = [os.path.dirname(sys.executable),] + paths
        for p in paths:
            current_entry = PathEntry.create(p, is_root=True)
            path_entries[p] = current_entry
            if current_entry.is_dir:
                for child, child_entry in current_entry.children.items():
                    path_entries[child] = child_entry
        return cls(paths=path_entries)


@attr.s
class PythonVersion(object):
    major = attr.ib(default=0)
    minor = attr.ib(default=None)
    patch = attr.ib(default=None)
    is_prerelease = attr.ib(default=False)
    is_postrelease = attr.ib(default=False)
    is_devrelease = attr.ib(default=False)
    version = attr.ib(default=None, validator=optional_instance_of(Version))
    comes_from = attr.ib(default=None, validator=optional_instance_of(PathEntry))

    @property
    def version_tuple(self):
        return (self.major, self.minor, self.patch, self.is_prerelease, self.is_devrelease)

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
        version = parse_version(version)
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
        if not isinstance(path, PathEntry):
            path = PathEntry(path)
        if not path.is_python:
            raise ValueError('Not a valid python path: %s' % path.path)
        try:
            instance_dict = cls.parse(get_python_version(str(path.path)))
        except subprocess.CalledProcessError:
            raise ValueError('Not a valid python path: %s' % path.path)
        instance_dict.update({'comes_from': path})
        return cls(**instance_dict)

    @classmethod
    def create(cls, **kwargs):
        return cls(**kwargs)
