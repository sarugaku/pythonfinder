from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

VERSION_RE = re.compile(
    r"(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>(?<=\.)[0-9]+))?\.?"
    r"(?:(?P<prerel>[abc]|rc|dev)(?:(?P<prerelversion>\d+(?:\.\d+)*))?)"
    r"?(?P<postdev>(\.post(?P<post>\d+))?(\.dev(?P<dev>\d+))?)?"
)
WINDOWS = sys.platform == "win32"
MACOS = sys.platform == "darwin"
PYTHON_IMPLEMENTATIONS = (
    "python",
    "ironpython",
    "jython",
    "pypy",
    "anaconda",
    "miniconda",
    "stackless",
    "activepython",
    "pyston",
    "micropython",
)
PY_MATCH_STR = (
    r"((?P<implementation>{0})(?:\d?(?:\.\d[cpm]{{0,3}}))?(?:-?[\d\.]+)*(?!w))$".format(
        "|".join(PYTHON_IMPLEMENTATIONS)
    )
)
RE_MATCHER = re.compile(PY_MATCH_STR)

if WINDOWS:
    KNOWN_EXTS = ("exe", "py", "bat", "")
else:
    KNOWN_EXTS = ("sh", "bash", "csh", "zsh", "fish", "py", "")


def path_is_readable(path: Path) -> bool:
    """Return True if the path is readable."""
    return os.access(str(path), os.R_OK)


@lru_cache(maxsize=1024)
def path_is_known_executable(path: Path) -> bool:
    """
    Returns whether a given path is a known executable from known executable extensions
    or has the executable bit toggled.

    :param path: The path to the target executable.
    :type path: :class:`~Path`
    :return: True if the path has chmod +x, or is a readable, known executable extension.
    :rtype: bool
    """
    return (
        os.access(str(path), os.X_OK)
        or os.access(str(path), os.R_OK)
        and path.suffix in KNOWN_EXTS
    )


@lru_cache(maxsize=1024)
def looks_like_python(name: str) -> bool:
    """
    Determine whether the supplied filename looks like a possible name of python.

    :param str name: The name of the provided file.
    :return: Whether the provided name looks like python.
    :rtype: bool
    """
    if not any(name.lower().startswith(py_name) for py_name in PYTHON_IMPLEMENTATIONS):
        return False
    match = RE_MATCHER.match(name)
    return bool(match)


@lru_cache(maxsize=1024)
def path_is_python(path: Path) -> bool:
    """
    Determine whether the supplied path is a executable and looks like
    a possible path to python.

    :param path: The path to an executable.
    :type path: :class:`~Path`
    :return: Whether the provided path is an executable path to python.
    :rtype: bool
    """
    if not path_is_readable(path) or not path.resolve().is_file():
        return False
    return path_is_known_executable(path) and looks_like_python(path.name)


@lru_cache(maxsize=1024)
def subprocess_output(*args: str) -> str:
    """
    Run a command and return the output.

    :param cmd: The command to run.
    :type cmd: list[str]
    :return: The output of the command.
    :rtype: str
    """
    return subprocess.check_output(list(args)).decode("utf-8")


@lru_cache(maxsize=1024)
def get_binary_hash(path: Path) -> str:
    """Return the MD5 hash of the given file."""
    hasher = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_major(version: str) -> dict[str, int | bool | None] | None:
    """Parse the version dict from the version string"""
    match = VERSION_RE.match(version)
    if not match:
        return None
    rv = match.groupdict()
    rv["pre"] = bool(rv.pop("prerel"))
    rv["dev"] = bool(rv.pop("dev"))
    for int_values in ("major", "minor", "patch"):
        if rv[int_values] is not None:
            rv[int_values] = int(rv[int_values])
    return rv
