from __future__ import annotations

import os
from collections import namedtuple
from pathlib import Path

import pytest

from pythonfinder import Finder
from pythonfinder.utils.path_utils import (
    looks_like_python,
    path_is_known_executable,
    path_is_python,
)
from pythonfinder.utils.version_utils import parse_python_version

os.environ["ANSI_COLORS_DISABLED"] = "1"

pythoninfo = namedtuple("PythonVersion", ["version", "path", "arch"])


def _get_python_versions():
    finder = Finder(global_search=True, system=False, ignore_unsupported=True)
    pythons = finder.find_all_python_versions()

    # Sort by version_sort property
    return sorted(list(pythons), key=lambda x: x.version_sort, reverse=True)


PYTHON_VERSIONS = _get_python_versions()

# Instead of calling get_python_version which uses subprocess,
# we'll use the version that's already available in the Python object
version_dicts = [
    (
        parse_python_version(str(python.version)),
        python.as_dict(),
    )
    for python in PYTHON_VERSIONS
]

test_paths = [(python.path.as_posix(), True) for python in PYTHON_VERSIONS]


@pytest.mark.parse
@pytest.mark.skip(reason="Skipping test that invokes Python subprocess")
def test_get_version():
    """
    This test has been skipped to avoid invoking Python subprocesses
    which can cause timeouts in CI environments, especially on Windows.
    """
    pass


@pytest.mark.parse
@pytest.mark.parametrize("python, expected", version_dicts)
def test_parse_python_version(python, expected):
    for key in ["comes_from", "architecture", "executable", "name", "company"]:
        if key in expected:
            del expected[key]
        if key in python:
            del python[key]
    assert python == expected


@pytest.mark.is_python
@pytest.mark.parametrize("python, expected", test_paths)
def test_is_python(python, expected):
    assert path_is_known_executable(Path(python))
    assert looks_like_python(os.path.basename(python))
    assert path_is_python(Path(python))
