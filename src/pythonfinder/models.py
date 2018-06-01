# -*- coding=utf-8 -*-
import attr
import locale
import operator
import os
import platform
import subprocess
import sys
from collections import defaultdict
from fnmatch import fnmatch
from packaging.version import parse as parse_version, Version

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

from .environment import PYENV_INSTALLED, PYENV_ROOT

PYTHON_IMPLEMENTATIONS = (
    'python',
    'ironpython',
    'jython',
    'pypy',
)

KNOWN_EXTS = {'exe', 'py', 'fish', 'sh', ''}
KNOWN_EXTS = KNOWN_EXTS | set(filter(None, os.environ.get('PATHEXT', '').split(os.pathsep)))


def _run(cmd):
    """Use `subprocess.check_output` to get the output of a command and decode it.

    :param list cmd: A list representing the command you want to run.
    :returns: A 2-tuple of (output, error)
    """
    encoding = locale.getdefaultlocale()[1] or 'utf-8'
    env = os.environ.copy()
    c = subprocess.Popen(cmd, encoding=encoding, env=env, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = c.communicate()
    return output.strip(), err.strip()


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


class BasePath(object):

    def which(self, name):
        """Search in this path for an executable.

        :param executable: The name of an executable to search for.
        :type executable: str
        :returns: :class:`~pythonfinder.models.PathEntry` instance.
        """
        valid_names = ['{0}.{1}'.format(name, ext).lower() if ext else '{0}'.format(name).lower() for ext in KNOWN_EXTS]
        finder = filter(operator.attrgetter('is_executable'), self.children.values())
        name_getter = operator.attrgetter('path.name')
        return next((child for child in finder if name_getter(child).lower() in valid_names), None)


@attr.s
class PathEntry(BasePath):
    path = attr.ib(default=None, validator=optional_instance_of(Path))
    _children = attr.ib(default=attr.Factory(dict))
    is_root = attr.ib(default=True)
    only_python = attr.ib(default=False)

    def _filter_children(self):
        if self.only_python:
            children = filter(lambda x: PythonVersion.is_python_name(x.name), self.path.iterdir())
        else:
            children = self.path.iterdir()
        return children

    @property
    def children(self):
        if not self._children and self.is_dir and self.is_root:
            self._children = {
                child.as_posix(): PathEntry(path=child, is_root=False)
                for child in self._filter_children()
            }
        return self._children

    @classmethod
    def create(cls, path, is_root=False, only_python=False):
        return cls(path=Path(os.path.expandvars(str(path))), is_root=is_root, only_python=only_python)

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
        return self.is_executable and PythonVersion.is_python_name(self.path.name)


@attr.s
class SystemPath(object):
    paths = attr.ib(default=attr.Factory(defaultdict))
    _executables = attr.ib(default=attr.Factory(list))
    _python_executables = attr.ib(default=attr.Factory(list))
    path_order = attr.ib(default=attr.Factory(list))
    python_version_dict = attr.ib()
    only_python = attr.ib(default=False)
    pyenv_instance = attr.ib(default=None, validator=optional_instance_of('PyenvPath'))

    @property
    def executables(self):
        if not self._executables:
            self._executables = [p for p in self.paths.values() if p.is_executable]
        return self._executables

    @property
    def python_executables(self):
        if not self._python_executables:
            self._python_executables = [p for p in self.paths.values() if p.is_python]
        return self._python_executables

    @python_version_dict.default
    def get_python_version_dict(self):
        version_dict = defaultdict(list)
        for p in self.python_executables:
            try:
                version_object = PythonVersion.from_path(p)
            except ValueError:
                continue
            version_dict[version_object.version_tuple].append(version_object)
        return version_dict

    def __attrs_post_init__(self):
        #: slice in pyenv
        if PYENV_INSTALLED:
            last_pyenv = next((p for p in reversed(self.path_order) if PYENV_ROOT.lower() in p.lower()), None)
            pyenv_index = self.path_order.index(last_pyenv)
            self.pyenv_instance = PyenvPath.create(root=PYENV_ROOT)
            paths = (v.paths.values() for v in self.pyenv_instance.versions.values())
            root_paths = (p for path in paths for p in path if p.is_root)
            before_path = self.path_order[:pyenv_index+1]
            after_path = self.path_order[pyenv_index+2:]
            self.path_order = before_path + [p.path.as_posix() for p in root_paths] + after_path
            self.paths.update({
                p.path: p
                for p in root_paths
            })

    def get_path(self, path):
        _path = self.paths.get(path)
        if not _path and path in self.path_order:
            self.paths[path] = PathEntry.create(path=path, is_root=True, only_python=self.only_python)
        return self.paths.get(path)

    def which(self, executable):
        """Search for an executable on the path.

        :param executable: Name of the executable to be located.
        :type executable: str
        :returns: :class:`~pythonfinder.models.PathEntry` object.
        """
        sub_which = operator.methodcaller('which', name=executable)
        return next(filter(None, [sub_which(self.get_path(k)) for k in self.path_order]))

    @classmethod
    def create(cls, path=None, system=False, only_python=False):
        path_entries = defaultdict(PathEntry)
        paths = os.environ.get('PATH').split(os.pathsep)
        if path:
            paths = [path,] + paths
        if sys:
            paths = [os.path.dirname(sys.executable),] + paths
        path_entries.update({
            p: PathEntry.create(path=p, is_root=True, only_python=only_python)
            for p in paths
        })
        return cls(paths=path_entries, path_order=paths, only_python=only_python)


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

    @staticmethod
    def is_python_name(name):
        rules = ['*python', '*python?', '*python?.?', '*python?.?m']
        match_rules = []
        for rule in rules:
            match_rules.extend([
                '{0}.{1}'.format(rule, ext) if ext else '{0}'.format(rule) for ext in KNOWN_EXTS
            ])
        if not any(name.lower().startswith(py_name) for py_name in PYTHON_IMPLEMENTATIONS):
            return False
        return any(fnmatch(name, rule) for rule in match_rules)

    @classmethod
    def from_path(cls, path):
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
    def create(cls, **kwargs):
        return cls(**kwargs)


@attr.s
class PyenvVersion(SystemPath):
    base = attr.ib(default=None, validator=optional_instance_of(Path))

    def __attrs_post_init__(self):
        pass

    @classmethod
    def create(cls, base=None, only_python=True):
        """Accepts a path to the base pyenv version directory.

        Generates the pyenv version listings for it"""
        if not isinstance(base, Path):
            base = Path(base)
        path_entries = defaultdict(PathEntry)
        bin_dir = base / 'bin'
        current_entry = PathEntry.create(bin_dir, is_root=True, only_python=True)
        path_entries[bin_dir.as_posix()] = current_entry
        return cls(base=base, paths=path_entries)


@attr.s
class PyenvPath(object):
    root = attr.ib(default=None, validator=optional_instance_of(Path))
    versions = attr.ib()

    @versions.default
    def get_versions(self):
        versions = defaultdict(PyenvVersion)
        for p in self.root.glob('versions/*'):
            version = PythonVersion.parse(p.name)
            version_tuple = (
                version.get('major'),
                version.get('minor'),
                version.get('patch'),
                version.get('is_prerelease'),
                version.get('is_devrelease'),
            )
            versions[version_tuple] = PyenvVersion.create(base=p, only_python=True)
        return versions

    @classmethod
    def create(cls, root):
        if not isinstance(root, Path):
            root = Path(root)
        return cls(root=root)
