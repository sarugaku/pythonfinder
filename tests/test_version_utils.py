from __future__ import annotations

import subprocess
from unittest import mock

import pytest
from packaging.version import Version

from pythonfinder.exceptions import InvalidPythonVersion
from pythonfinder.utils.version_utils import (
    get_python_version,
    guess_company,
    parse_asdf_version_order,
    parse_pyenv_version_order,
    parse_python_version,
)


def test_get_python_version():
    """Test that get_python_version correctly gets the Python version."""
    # Test successful execution
    process_mock = mock.MagicMock()
    process_mock.communicate.return_value = ("3.8.0", "")

    with mock.patch("subprocess.Popen", return_value=process_mock):
        version = get_python_version("/usr/bin/python")
        assert version == "3.8.0"

    # Test with OSError
    with mock.patch("subprocess.Popen", side_effect=OSError):
        with pytest.raises(InvalidPythonVersion):
            get_python_version("/usr/bin/python")

    # Test with timeout
    process_mock = mock.MagicMock()
    process_mock.communicate.side_effect = subprocess.TimeoutExpired("cmd", 5)

    with mock.patch("subprocess.Popen", return_value=process_mock):
        with pytest.raises(InvalidPythonVersion):
            get_python_version("/usr/bin/python")

    # Test with empty output
    process_mock = mock.MagicMock()
    process_mock.communicate.return_value = ("", "")

    with mock.patch("subprocess.Popen", return_value=process_mock):
        with pytest.raises(InvalidPythonVersion):
            get_python_version("/usr/bin/python")


def test_parse_python_version():
    """Test that parse_python_version correctly parses Python version strings."""
    # Test standard version
    version_dict = parse_python_version("3.8.0")
    assert version_dict["major"] == 3
    assert version_dict["minor"] == 8
    assert version_dict["patch"] == 0
    assert version_dict["is_prerelease"] is False
    assert version_dict["is_postrelease"] is False
    assert version_dict["is_devrelease"] is False
    assert version_dict["is_debug"] is False
    assert version_dict["version"] == Version("3.8.0")

    # Test alpha pre-release
    version_dict = parse_python_version("3.8.0a1")
    assert version_dict["major"] == 3
    assert version_dict["minor"] == 8
    assert version_dict["patch"] == 0
    assert version_dict["is_prerelease"] is True
    assert version_dict["is_postrelease"] is False
    assert version_dict["is_devrelease"] is False
    assert version_dict["is_debug"] is False
    assert version_dict["version"] == Version("3.8.0a1")

    # Test release candidate pre-release
    version_dict = parse_python_version("3.8.0rc2")
    assert version_dict["major"] == 3
    assert version_dict["minor"] == 8
    assert version_dict["patch"] == 0
    assert version_dict["is_prerelease"] is True
    assert version_dict["is_postrelease"] is False
    assert version_dict["is_devrelease"] is False
    assert version_dict["is_debug"] is False
    assert version_dict["version"] == Version("3.8.0rc2")

    # Test post-release
    version_dict = parse_python_version("3.8.0.post1")
    assert version_dict["major"] == 3
    assert version_dict["minor"] == 8
    assert version_dict["patch"] == 0
    assert version_dict["is_prerelease"] is False
    assert version_dict["is_postrelease"] is True
    assert version_dict["is_devrelease"] is False
    assert version_dict["is_debug"] is False
    assert version_dict["version"] == Version("3.8.0.post1")

    # Test dev-release
    version_dict = parse_python_version("3.8.0.dev1")
    assert version_dict["major"] == 3
    assert version_dict["minor"] == 8
    assert version_dict["patch"] == 0
    assert version_dict["is_prerelease"] is False
    assert version_dict["is_postrelease"] is False
    assert version_dict["is_devrelease"] is True
    assert version_dict["is_debug"] is False
    assert version_dict["version"] == Version("3.8.0.dev1")

    # Test debug
    version_dict = parse_python_version("3.8.0-debug")
    assert version_dict["major"] == 3
    assert version_dict["minor"] == 8
    assert version_dict["patch"] == 0
    assert version_dict["is_prerelease"] is False
    assert version_dict["is_postrelease"] is False
    assert version_dict["is_devrelease"] is False
    assert version_dict["is_debug"] is True
    assert version_dict["version"] == Version("3.8.0")

    # Test complex version
    version_dict = parse_python_version("3.8.0rc1.post1.dev1")
    assert version_dict["major"] == 3
    assert version_dict["minor"] == 8
    assert version_dict["patch"] == 0
    assert version_dict["is_prerelease"] is True
    assert version_dict["is_postrelease"] is True
    assert version_dict["is_devrelease"] is True
    assert version_dict["is_debug"] is False
    assert version_dict["version"] == Version("3.8.0rc1.post1.dev1")

    # Test invalid version
    with pytest.raises(InvalidPythonVersion):
        parse_python_version("not-a-version")


def test_guess_company():
    """Test that guess_company correctly guesses the company from a path."""
    # Test PythonCore
    assert guess_company("/usr/bin/python") == "PythonCore"

    # Test other implementations
    assert guess_company("/usr/bin/pypy") == "pypy"
    assert guess_company("/usr/bin/jython") == "jython"
    assert guess_company("/usr/bin/anaconda3") == "anaconda"
    assert guess_company("/usr/bin/miniconda3") == "miniconda"

    # Test case insensitivity
    assert guess_company("/usr/bin/PyPy") == "pypy"
    assert guess_company("/usr/bin/JYTHON") == "jython"
    assert guess_company("/usr/bin/Anaconda3") == "anaconda"


def test_parse_pyenv_version_order():
    """Test that parse_pyenv_version_order correctly parses pyenv version order."""
    # Test with existing file
    with mock.patch("os.path.expanduser", return_value="/home/user"):
        with mock.patch("os.path.expandvars", return_value="/home/user/.pyenv"):
            with mock.patch("os.path.exists", return_value=True):
                with mock.patch("os.path.isfile", return_value=True):
                    with mock.patch(
                        "builtins.open", mock.mock_open(read_data="3.8.0\n3.7.0\n3.6.0")
                    ):
                        versions = parse_pyenv_version_order()
                        assert versions == ["3.8.0", "3.7.0", "3.6.0"]

    # Test with non-existing file
    with mock.patch("os.path.expanduser", return_value="/home/user"):
        with mock.patch("os.path.expandvars", return_value="/home/user/.pyenv"):
            with mock.patch("os.path.exists", return_value=False):
                versions = parse_pyenv_version_order()
                assert versions == []

    # Test with directory instead of file
    with mock.patch("os.path.expanduser", return_value="/home/user"):
        with mock.patch("os.path.expandvars", return_value="/home/user/.pyenv"):
            with mock.patch("os.path.exists", return_value=True):
                with mock.patch("os.path.isfile", return_value=False):
                    versions = parse_pyenv_version_order()
                    assert versions == []


def test_parse_asdf_version_order():
    """Test that parse_asdf_version_order correctly parses asdf version order."""
    # Test with existing file and python section
    with mock.patch("os.path.expanduser", return_value="/home/user"):
        with mock.patch("os.path.exists", return_value=True):
            with mock.patch("os.path.isfile", return_value=True):
                with mock.patch(
                    "builtins.open",
                    mock.mock_open(read_data="python 3.8.0 3.7.0 3.6.0\nruby 2.7.0"),
                ):
                    versions = parse_asdf_version_order()
                    assert versions == ["3.8.0", "3.7.0", "3.6.0"]

    # Test with existing file but no python section
    with mock.patch("os.path.expanduser", return_value="/home/user"):
        with mock.patch("os.path.exists", return_value=True):
            with mock.patch("os.path.isfile", return_value=True):
                with mock.patch(
                    "builtins.open", mock.mock_open(read_data="ruby 2.7.0\nnode 14.0.0")
                ):
                    versions = parse_asdf_version_order()
                    assert versions == []

    # Test with non-existing file
    with mock.patch("os.path.expanduser", return_value="/home/user"):
        with mock.patch("os.path.exists", return_value=False):
            versions = parse_asdf_version_order()
            assert versions == []

    # Test with directory instead of file
    with mock.patch("os.path.expanduser", return_value="/home/user"):
        with mock.patch("os.path.exists", return_value=True):
            with mock.patch("os.path.isfile", return_value=False):
                versions = parse_asdf_version_order()
                assert versions == []
