from __future__ import annotations

import atexit
import itertools
import os
import shutil
import stat
import tempfile
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import AnyStr

import click

TRACKED_TEMPORARY_DIRECTORIES = []


def set_write_bit(fn: str) -> None:
    """
    Set read-write permissions for the current user on the target path.  Fail silently
    if the path doesn't exist.

    :param str fn: The target filename or path
    :return: None
    """

    if not os.path.exists(fn):
        return
    file_stat = os.stat(fn).st_mode
    os.chmod(fn, file_stat | stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    if not os.path.isdir(fn):
        for path in [fn, os.path.dirname(fn)]:
            try:
                os.chflags(path, 0)
            except AttributeError:
                pass
        return None
    for root, dirs, files in os.walk(fn, topdown=False):
        for dir_ in [os.path.join(root, d) for d in dirs]:
            set_write_bit(dir_)
        for file_ in [os.path.join(root, f) for f in files]:
            set_write_bit(file_)


def create_tracked_tempdir(*args, **kwargs):
    """Create a tracked temporary directory.

    This uses ``tempfile.mkdtemp``, but does not remove the directory when
    the return value goes out of scope, instead registers a handler to cleanup
    on program exit.

    The return value is the path to the created directory.
    """

    tempdir = tempfile.mkdtemp(*args, **kwargs)
    TRACKED_TEMPORARY_DIRECTORIES.append(tempdir)
    atexit.register(shutil.rmtree, tempdir)
    warnings.simplefilter("ignore", ResourceWarning)
    return tempdir


@contextmanager
def cd(path):
    if not path:
        return
    prev_cwd = Path.cwd().as_posix()
    if isinstance(path, Path):
        path = path.as_posix()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@contextmanager
def temp_environ():
    """Allow the ability to set os.environ temporarily"""
    environ = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(environ)


def normalize_path(path: AnyStr) -> AnyStr:
    """
    Return a case-normalized absolute variable-expanded path.

    :param str path: The non-normalized path
    :return: A normalized, expanded, case-normalized path
    :rtype: str
    """

    path = os.path.abspath(os.path.expandvars(os.path.expanduser(str(path))))
    if os.name == "nt" and os.path.exists(path):
        try:
            from ctypes import create_unicode_buffer, windll
        except ImportError:
            path = os.path.normpath(os.path.normcase(path))
        else:
            BUFSIZE = 500
            buffer = create_unicode_buffer(BUFSIZE)
            get_long_path_name = windll.kernel32.GetLongPathNameW
            get_long_path_name(path.decode(), buffer, BUFSIZE)
            path = buffer.value
        return path

    return os.path.normpath(os.path.normcase(path))


def is_in_path(path: AnyStr, parent: AnyStr) -> bool:
    """
    Determine if the provided full path is in the given parent root.

    :param str path: The full path to check the location of.
    :param str parent: The parent path to check for membership in
    :return: Whether the full path is a member of the provided parent.
    :rtype: bool
    """

    return normalize_path(str(path)).startswith(normalize_path(str(parent)))


def normalized_match(path, parent):
    return is_in_path(normalize_path(path), normalize_path(parent))


def is_in_ospath(path):
    ospath = os.environ["PATH"].split(os.pathsep)
    return any(normalized_match(path, entry) for entry in ospath)


def print_python_versions(versions):
    versions = list(versions)
    if versions:
        click.echo("Found python at the following locations:", err=True)
        for v in versions:
            py = v.py_version
            comes_from = getattr(py, "comes_from", None)
            if comes_from is not None:
                comes_from_path = getattr(comes_from, "path", v.path)
            else:
                comes_from_path = v.path
            click.echo(
                "{py.name!s}: {py.version!s} ({py.architecture!s}) @ {comes_from!s}".format(
                    py=py, comes_from=comes_from_path
                ),
                err=True,
            )


STACKLESS = [("stackless-2.7.14", "2.7.14"), ("stackless-3.5.4", "3.5.4")]
PYPY = [
    ("pypy2.7-5.10.0", "2.7"),
    ("pypy2.7-6.0.0", "2.7"),
    ("pypy3.5-5.10.1", "3.5"),
    ("pypy3.5-6.0.0", "3.5"),
]
# These are definitely no longer supported but people may still have them installed
# PYSTON = [("pyston-0.5.1", "2.7.8"), ("pyston-0.6.0", "2.7.8"), ("pyston-0.6.1", "2.7.8")]
MINICONDA = [
    ("miniconda3-3.18.3", "3.5.4"),
    ("miniconda3-3.19.0", "3.5.5"),
    ("miniconda3-4.0.5", "3.6.2"),
    ("miniconda3-4.1.11", "3.6.2"),
    ("miniconda3-4.3.27", "3.7.1"),
    ("miniconda3-4.3.30", "3.7.2"),
]
# I have no idea how these are represented
# MICROPYTHON = [("micropython-1.9.3", "1.9.3"), ("micropython-1.9.4", "1.9.4")]
JYTHON = [
    # ("jython-2.5-dev", "2.5-dev"),
    # ("jython-2.5.1", "2.5.1"),
    # ("jython-2.5.2", "2.5.2"),
    # ("jython-2.5.3", "2.5.3"),
    # ("jython-2.5.4-rc1", "2.5.4-rc1"),
    # ("jython-2.7.0", "2.7.0"),
    ("jython-2.7.1", "2.7.1")
]
ANACONDA = [
    ("anaconda2-2.4.1", "2.7.8"),
    ("anaconda2-2.5.0", "2.7.10"),
    ("anaconda2-4.0.0", "2.7.12"),
    ("anaconda2-4.1.0", "2.7.13"),
    ("anaconda2-4.1.1", "2.7.13"),
    ("anaconda2-4.2.0", "2.7.14"),
    ("anaconda2-4.3.0", "2.7.14"),
    ("anaconda2-4.3.1", "2.7.15"),
    ("anaconda2-4.4.0", "2.7.15"),
    ("anaconda3-4.1.1", "3.4.5"),
    ("anaconda3-4.2.0", "3.5.2"),
    ("anaconda3-4.3.0", "3.5.3"),
    ("anaconda3-4.3.1", "3.5.4"),
    ("anaconda3-4.4.0", "3.5.5"),
    ("anaconda3-5.0.0", "3.6.2"),
    ("anaconda3-5.0.1", "3.6.2"),
    ("anaconda3-5.1.0", "3.6.3"),
    ("anaconda3-5.2.0", "3.6.4"),
    ("anaconda3-5.3.0", "3.6.5"),
    ("anaconda3-2019.03", "3.7.2"),
]
IRONPYTHON = [
    # ("ironpython-dev", "2.7.8"),
    # ("ironpython-2.7.4", "2.7.4"),
    # ("ironpython-2.7.5", "2.7.5"),
    # ("ironpython-2.7.6.3", "2.7.6"),
    ("ironpython-2.7.7", "2.7.7")
]
ACTIVEPYTHON = [
    ("activepython-2.7.14", "2.7.14"),
    ("activepython-3.5.4", "3.5.4"),
    ("activepython-3.6.0", "3.6.0"),
]
PYTHON = [
    ("2.7.14", "2.7.14"),
    ("2.7.15", "2.7.15"),
    ("3.6.6", "3.6.6"),
    ("3.6.7", "3.6.7"),
    ("3.6.8", "3.6.8"),
    ("3.7.0", "3.7.0"),
    ("3.7-dev", "3.7-dev"),
    ("3.7.1", "3.7.1"),
    ("3.7.2", "3.7.2"),
    ("3.7.3", "3.7.3"),
    ("3.8-dev", "3.8-dev"),
]


def yield_versions():
    return itertools.chain(
        STACKLESS,
        PYPY,
        # PYSTON,
        MINICONDA,
        # MICROPYTHON,
        JYTHON,
        ANACONDA,
        IRONPYTHON,
        ACTIVEPYTHON,
        PYTHON,
    )
