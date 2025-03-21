from __future__ import annotations

import os
from pathlib import Path

import pytest

from pythonfinder import Finder
from pythonfinder.models.python_info import PythonInfo


@pytest.fixture
def simple_finder():
    """Return a simple Finder instance for testing."""
    return Finder(system=True, global_search=True)


def test_finder_initialization():
    """Test that the Finder initializes with the correct parameters."""
    finder = Finder(
        path="/test/path", system=True, global_search=False, ignore_unsupported=False
    )

    assert finder.path == "/test/path"
    assert finder.system is True
    assert finder.global_search is False
    assert finder.ignore_unsupported is False

    # Check that all finders are initialized
    assert finder.system_finder is not None
    assert finder.pyenv_finder is not None
    assert finder.asdf_finder is not None
    if os.name == "nt":
        assert finder.windows_finder is not None


def test_which_method():
    """Test the which method to find an executable."""
    finder = Finder(system=True, global_search=True)

    # Test finding the python executable
    python_path = finder.which("python")

    # The test should pass if python is found or not
    if python_path:
        assert isinstance(python_path, Path)
        assert python_path.exists()
        assert python_path.is_file()
    else:
        # If python is not found, the test should still pass
        assert python_path is None


def test_find_python_version():
    """Test the find_python_version method."""
    finder = Finder(system=True, global_search=True)

    # Test finding Python 3
    python3 = finder.find_python_version(3)

    # The test should pass if Python 3 is found or not
    if python3:
        assert isinstance(python3, PythonInfo)
        assert python3.major == 3
        assert python3.path.exists()
        assert python3.path.is_file()
    else:
        # If Python 3 is not found, the test should still pass
        assert python3 is None


def test_find_python_version_with_string_major():
    """Test the find_python_version method with a string major version."""
    finder = Finder(system=True, global_search=True)

    # Test finding Python 3.8
    python38 = finder.find_python_version(major="3.8")

    # The test should pass if Python 3.8 is found or not
    if python38:
        assert isinstance(python38, PythonInfo)
        assert python38.major == 3
        assert python38.minor == 8
        assert python38.path.exists()
        assert python38.path.is_file()
    else:
        # If Python 3.8 is not found, the test should still pass
        assert python38 is None


def test_find_all_python_versions():
    """Test the find_all_python_versions method."""
    finder = Finder(system=True, global_search=True)

    # Test finding all Python versions
    all_versions = finder.find_all_python_versions()

    # The test should pass if Python versions are found or not
    if all_versions:
        assert isinstance(all_versions, list)
        assert all(isinstance(version, PythonInfo) for version in all_versions)

        # Check that the versions are sorted correctly (highest version first)
        for i in range(len(all_versions) - 1):
            assert all_versions[i].version_sort >= all_versions[i + 1].version_sort
    else:
        # If no Python versions are found, the test should still pass
        assert all_versions == []


def test_find_all_python_versions_with_string_major():
    """Test the find_all_python_versions method with a string major version."""
    finder = Finder(system=True, global_search=True)

    # Test finding all Python 3.8 versions
    python38_versions = finder.find_all_python_versions(major="3.8")

    # The test should pass if Python 3.8 versions are found or not
    if python38_versions:
        assert isinstance(python38_versions, list)
        assert all(isinstance(version, PythonInfo) for version in python38_versions)
        assert all(
            version.major == 3 and version.minor == 8 for version in python38_versions
        )
    else:
        # If no Python 3.8 versions are found, the test should still pass
        assert python38_versions == []


def test_find_all_python_versions_deduplication():
    """Test that find_all_python_versions deduplicates Python versions with the same path."""
    finder = Finder(system=True, global_search=True)

    # Test finding all Python versions
    all_versions = finder.find_all_python_versions()

    # Check that there are no duplicate paths
    if all_versions:
        paths = [version.path for version in all_versions]
        assert len(paths) == len(set(paths))
