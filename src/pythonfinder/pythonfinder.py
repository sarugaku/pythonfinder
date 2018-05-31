# -*- coding=utf-8 -*-
import os
import sys
import delegator
import platform
from packaging.version import parse as parse_version
from collections import defaultdict
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


PYENV_INSTALLED = (bool(os.environ.get('PYENV_SHELL')) or bool(os.environ.get('PYENV_ROOT')))
PYENV_ROOT = os.environ.get('PYENV_ROOT', os.path.expanduser('~/.pyenv'))
IS_64BIT_OS = None
SYSTEM_ARCH = platform.architecture()[0]

if sys.maxsize > 2**32:
    IS_64BIT_OS = (platform.machine() == 'AMD64')
else:
    IS_64BIT_OS = False


def shellquote(s):
    """Prepares a string for the shell (on Windows too!)

    Only for use on grouped arguments (passed as a string to Popen)
    """
    if s is None:
        return None
    # Additional escaping for windows paths
    if os.name == 'nt':
        s = "{}".format(s.replace("\\", "\\\\"))

    return '"' + s.replace("'", "'\\''") + '"'


class PathFinder(object):
    WHICH = {}
    PATH = None

    def __init__(self, path=None, system=False):
        """A generic object for locating files on the system path.

        :param str path: OS Formatted path to prepend to OS environment, defaults to None
        :param bool system: When true, append paths instead of prepending, defaults to False
        """

        search = os.environ.get('PATH')
        if path:
            if system:
                path = os.pathsep.join([os.path.dirname(sys.executable), search, path])
            else:
                path = os.pathsep.join([path, search])
        else:
            if system:
                path = os.pathsep.join([os.path.dirname(sys.executable), search])
        PathFinder.PATH = path if path else os.environ.get('PATH')
        self._populate_which_dict()

    @classmethod
    def which(cls, cmd):
        """Find a system executable, respecting the set order of the path provided.

        :param cmd: The command to search for.
        :type cmd: str
        :return: The path to the command requested.
        :rtype: str
        """

        if not cls.WHICH:
            cls._populate_which_dict()
        return cls.WHICH.get(cmd, cmd)

    @classmethod
    def _populate_which_dict(cls):
        for path in cls.PATH.split(os.pathsep):
            path = os.path.expandvars(path)
            try:
                files = os.listdir(path)
            except OSError:
                continue
            for fn in files:
                full_path = os.sep.join([path, fn])
                if os.access(full_path, os.X_OK) and not os.path.isdir(full_path):
                    if not cls.WHICH.get(fn):
                        cls.WHICH[fn] = full_path
                    base_exec = os.path.splitext(fn)[0]
                    if not cls.WHICH.get(base_exec):
                        cls.WHICH[base_exec] = full_path


class PythonFinder(PathFinder):
    """Find pythons given a specific version, path, or nothing."""

    PYENV_VERSIONS = {}
    PYTHON_VERSIONS = {}
    PYTHON_PATHS = {}
    MAX_PYTHON = {}
    PYTHON_ARCHS = defaultdict(dict)
    WHICH_PYTHON = {}
    RUNTIMES = ['python', 'pypy', 'ipy', 'jython', 'pyston']

    def __init__(self, path=None, venv=None, system=False, version=None, full_version=None):
        """Finder class for finding python and related executables across platforms/envs.

        :param path: OS formatted path to prepend to os.environ['PATH'], defaults to None
        :param path: str, optional
        :param venv: Virtualenv root to search, prepends bin directory to path, defaults to None
        :param venv: str, optional
        :param system: When `True`, append to the path instead of prepending, defaults to False
        :param system: bool, optional
        :param version: Python version to search for, defaults to None
        :param version: str, optional
        :param full_version: Full python version to search for, defaults to None
        :param full_version: str, optional
        """

        self.version = version
        if venv:
            bin_dir = 'Scripts' if os.name == 'nt' else 'bin'
            venv_search_loc = os.path.abspath(os.path.join(venv, bin_dir))
            if path:
                path = os.pathsep.join([venv_search_loc, path])
            else:
                path = venv_search_loc
        self.full_version = full_version
        super(PythonFinder, self).__init__(path=path, system=system)

    def get_pyenv_versions(self):
        """Refresh the internal mapping of pyenv runtimes and return a map of versions to paths.

        :return: A dictionary mapping pyenv versions to respective paths.
        :rtype: dict
        """

        if not PYENV_INSTALLED:
            return {}
        self._populate_pyenv_runtimes()
        return self.PYENV_VERSIONS

    def get_python_paths(self):
        """Refresh python path mapping and return it.

        :return: A mapping of python paths to python versions.
        :rtype: dict
        """

        if not self.PYTHON_PATHS:
            if os.name == 'nt':
                self._populate_windows_python_versions()
            else:
                self._populate_python_versions()
        return self.PYTHON_PATHS

    @classmethod
    def from_line(cls, python):
        """Given an ambiguous python line (path, launcher input, or exe name), find it and return its path.

        :param python: Ambiguous input referring to a python executable of some kind.
        :type python: str
        :return: Path to the referenced python executable.
        :rtype: str
        """

        if os.path.isabs(python) and os.access(python, os.X_OK):
            return python
        if python.startswith('py'):
            windows_finder = python.split()
            if len(windows_finder) > 1 and windows_finder[0] == 'py' and windows_finder[1].startswith('-'):
                version = windows_finder[1].strip('-').split()[0]
                return cls.from_version(version)
            return cls.WHICH_PYTHON.get(python) or cls.which(python)

    @classmethod
    def from_version(cls, version, architecture=None):
        """Given a version specifier, find the matching path on the filesystem and return it.

        :param version: A version of python.
        :type version: str
        :param architecture: System architecture (windows only), defaults to None
        :param architecture: str, optional
        :return: Path to python executable.
        :rtype: :class:`pathlib.Path`

        For example:

          ::

            >>> PythonFinder.from_version('2.7', architecture='64bit')
            WindowsPath('C:/Python27/python.exe')
        """

        guess = cls.PYTHON_VERSIONS.get(cls.MAX_PYTHON.get(version, version))
        if guess:
            return guess
        if os.name == 'nt':
            path = cls.from_windows_finder(version, architecture)
        else:
            parsed_version = parse_version(version)
            full_version = parsed_version.base_version
            if PYENV_INSTALLED:
                path = cls.from_pyenv(full_version)
            else:
                path = cls._crawl_path_for_version(full_version)
        if path and not isinstance(path, Path):
            path = Path(path)
        return path

    @classmethod
    def from_windows_finder(cls, version=None, arch=None):
        if not cls.PYTHON_VERSIONS:
            cls._populate_windows_python_versions()
        if arch:
            return cls.PYTHON_ARCHS[version][arch]
        return cls.PYTHON_VERSIONS[version]

    @classmethod
    def _populate_windows_python_versions(cls):
        from pythonfinder._vendor.pep514tools import environment
        versions = environment.findall()
        path = None
        for version_object in versions:
            path = Path(version_object.info.install_path.__getattr__('')).joinpath('python.exe')
            version = version_object.info.sys_version
            full_version = version_object.info.version
            architecture = getattr(version_object, 'sys_architecture', SYSTEM_ARCH)
            for v in [version, full_version, architecture]:
                if not cls.PYTHON_VERSIONS.get(v):
                    cls.PYTHON_VERSIONS[v] = '{0}'.format(path)
            cls.register_python(path, full_version, architecture)

    @classmethod
    def _populate_python_versions(cls):
        import fnmatch
        match_rules = ['*python', '*python?', '*python?.?', '*python?.?m']
        runtime_execs = []
        exts = list(filter(None, os.environ.get('PATHEXT', '').split(os.pathsep)))
        for path in cls.PATH.split(os.pathsep):
            path = os.path.expandvars(path)
            from glob import glob
            pythons = glob(os.sep.join([path, 'python*']))
            execs = [match for rule in match_rules for match in fnmatch.filter(pythons, rule)]
            for executable in execs:
                exec_name = os.path.basename(executable)
                if os.access(executable, os.X_OK):
                    runtime_execs.append(executable)
                if not cls.WHICH_PYTHON.get(exec_name):
                    cls.WHICH_PYTHON[exec_name] = executable
                for e in exts:
                    pext = executable + e
                    if os.access(pext, os.X_OK):
                        runtime_execs.append(pext)
        for python in runtime_execs:
            version_cmd = '{0} -c "import sys; print(sys.version.split()[0])"'.format(shellquote(python))
            version = delegator.run(version_cmd).out.strip()
            cls.register_python(python, version)

    @classmethod
    def _crawl_path_for_version(cls, version):
        if not cls.PYTHON_VERSIONS:
            cls._populate_python_versions()
        return cls.PYTHON_VERSIONS.get(version)

    @classmethod
    def from_pyenv(cls, version):
        if not cls.PYENV_VERSIONS:
            cls.populate_pyenv_runtimes()
        return cls.PYENV_VERSIONS[version]

    @classmethod
    def register_python(cls, path, full_version, pre=False, pyenv=False, arch=None):
        if not arch:
            import platform
            arch, _ = platform.architecture()
        parsed_version = parse_version(full_version)
        if isinstance(parsed_version._version, str):
            if arch == SYSTEM_ARCH or SYSTEM_ARCH.startswith(str(arch)):
                cls.PYTHON_VERSIONS[parsed_version._version] = path
            cls.MAX_PYTHON[parsed_version._version] = parsed_version._version
            cls.PYTHON_VERSIONS[parsed_version._version] = parsed_version._version
            cls.PYTHON_PATHS[path] = parsed_version._version
            cls.PYTHON_ARCHS[parsed_version._version][arch] = path
            return
        pre = pre or parsed_version.is_prerelease
        major_minor = '.'.join(['{0}'.format(v) for v in parsed_version._version.release[:2]])
        major = '{0}'.format(parsed_version._version.release[0])
        cls.PYTHON_PATHS[path] = full_version
        if not pre and parsed_version > parse_version(cls.MAX_PYTHON.get(major_minor, '0.0.0')):
            if major_minor != full_version:
                if parsed_version > parse_version(cls.MAX_PYTHON.get(full_version, '0.0.0')):
                    cls.MAX_PYTHON[full_version] = parsed_version.base_version
            cls.MAX_PYTHON[major_minor] = parsed_version.base_version
            cls.PYTHON_VERSIONS[major_minor] = path
            if arch == SYSTEM_ARCH or SYSTEM_ARCH.startswith(str(arch)):
                if parsed_version > parse_version(cls.MAX_PYTHON.get(major, '0.0.0')):
                    cls.MAX_PYTHON[major] = parsed_version.base_version
                    cls.PYTHON_VERSIONS[major] = path
        if not pyenv:
            for v in [full_version, major_minor, major]:
                if not cls.PYTHON_VERSIONS.get(v) or cls.MAX_PYTHON.get(v) == full_version:
                    if cls.MAX_PYTHON.get(v) == full_version and not (arch == SYSTEM_ARCH or SYSTEM_ARCH.startswith(str(arch))):
                        pass
                    else:
                        cls.PYTHON_VERSIONS[v] = path
                if not cls.PYTHON_ARCHS.get(v, {}).get(arch):
                    cls.PYTHON_ARCHS[v][arch] = path
        else:
            for v in [full_version, major_minor, major]:
                if (not cls.PYENV_VERSIONS.get(v) and (v == major and not pre) or v != major) or cls.MAX_PYTHON.get(v) == full_version:
                    cls.PYENV_VERSIONS[v] = path
            if not cls.PYTHON_VERSIONS.get(full_version):
                cls.PYTHON_VERSIONS[full_version] = path
            if not cls.PYTHON_ARCHS.get(v, {}).get(arch):
                    cls.PYTHON_ARCHS[v][arch] = path

    @classmethod
    def populate_pyenv_runtimes(cls):
        from glob import glob
        search_path = os.sep.join(['{0}'.format(PYENV_ROOT), 'versions', '*'])
        runtimes = ['pypy', 'ipy', 'jython', 'pyston']
        for pyenv_path in glob(search_path):
            parsed_version = parse_version(os.path.basename(pyenv_path))
            if parsed_version.is_prerelease and cls.PYENV_VERSIONS.get(parsed_version.base_version):
                continue
            bin_path = os.sep.join([pyenv_path, 'bin'])
            runtime = os.sep.join([bin_path, 'python'])
            if not os.path.exists(runtime):
                exes = [os.sep.join([bin_path, exe]) for exe in runtimes if os.path.exists(os.sep.join([bin_path, exe]))]
                if exes:
                    runtime = exes[0]
            cls.register_python(runtime, parsed_version.base_version, pre=parsed_version.is_prerelease, pyenv=True)
