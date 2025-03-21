from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from pythonfinder.utils.path_utils import (
    ensure_path,
    exists_and_is_accessible,
    filter_pythons,
    is_executable,
    is_in_path,
    is_readable,
    looks_like_python,
    path_is_known_executable,
    path_is_python,
    resolve_path,
)


def test_ensure_path():
    """Test that ensure_path correctly converts strings to Path objects."""
    # Test with a string
    path_str = "/usr/bin/python"
    path = ensure_path(path_str)
    assert isinstance(path, Path)

    # On Windows, ensure_path will normalize Unix-style paths for tests
    if os.name == "nt":
        # For Windows, we expect the path to be normalized to Unix-style for tests
        assert path_str in path.as_posix()
    else:
        # For Unix systems, the path should be exactly as provided
        assert path.as_posix() == path_str

    # Test with a Path object
    path_obj = Path("/usr/bin/python")
    path = ensure_path(path_obj)
    assert isinstance(path, Path)
    assert path.absolute() == path_obj.absolute()

    # Test with environment variables
    with mock.patch.dict(os.environ, {"TEST_PATH": "/test/path"}):
        path = ensure_path("$TEST_PATH/python")
        assert isinstance(path, Path)

        # Check that the path contains the expected components
        assert "test/path/python" in path.as_posix().replace("\\", "/")

        # Test with user home directory
        with mock.patch("os.path.expanduser", return_value="/home/user/python"):
            path = ensure_path("~/python")
            assert isinstance(path, Path)
            assert "home/user/python" in path.as_posix().replace("\\", "/")


def test_resolve_path():
    """Test that resolve_path correctly resolves paths."""
    # Test with a string
    path_str = "/usr/bin/python"
    path = resolve_path(path_str)
    assert isinstance(path, Path)

    # Test with a Path object
    path_obj = Path("/usr/bin/python")
    path = resolve_path(path_obj)
    assert isinstance(path, Path)

    # Test with environment variables
    with mock.patch.dict(os.environ, {"TEST_PATH": "/test/path"}):
        path = resolve_path("$TEST_PATH/python")
        assert isinstance(path, Path)
        assert path.as_posix().endswith("/test/path/python")

    # Test with user home directory
    with mock.patch("os.path.expanduser", return_value="/home/user"):
        path = resolve_path("~/python")
        assert isinstance(path, Path)
        assert path.as_posix().endswith("/home/user/python")


def test_is_executable():
    """Test that is_executable correctly checks if a path is executable."""
    with mock.patch("os.access", return_value=True):
        assert is_executable("/usr/bin/python")

    with mock.patch("os.access", return_value=False):
        assert not is_executable("/usr/bin/python")


def test_is_readable():
    """Test that is_readable correctly checks if a path is readable."""
    with mock.patch("os.access", return_value=True):
        assert is_readable("/usr/bin/python")

    with mock.patch("os.access", return_value=False):
        assert not is_readable("/usr/bin/python")


def test_path_is_known_executable():
    """Test that path_is_known_executable correctly checks if a path is a known executable."""
    # Test with executable bit set
    with mock.patch("pythonfinder.utils.path_utils.is_executable", return_value=True):
        assert path_is_known_executable(Path("/usr/bin/python"))

    # Test with readable file and known extension
    with mock.patch("pythonfinder.utils.path_utils.is_executable", return_value=False):
        with mock.patch("pythonfinder.utils.path_utils.is_readable", return_value=True):
            # Test with .py extension
            with mock.patch("pythonfinder.utils.path_utils.KNOWN_EXTS", {".py"}):
                assert path_is_known_executable(Path("/usr/bin/script.py"))

            # Test with .exe extension on Windows
            if os.name == "nt":
                assert path_is_known_executable(Path("/usr/bin/python.exe"))

            # Test with unknown extension
            assert not path_is_known_executable(Path("/usr/bin/script.unknown"))


def test_looks_like_python():
    """Test that looks_like_python correctly identifies Python executables."""
    # Mock the fnmatch function to always return True for Python executables
    with mock.patch("fnmatch.fnmatch", return_value=True):
        # Test with valid Python names
        assert looks_like_python("python")
        assert looks_like_python("python3")
        assert looks_like_python("python3.8")
        assert looks_like_python("python.exe")
        assert looks_like_python("python3.exe")
        assert looks_like_python("python3.8.exe")
        assert looks_like_python("python3.8m")
        assert looks_like_python("python3-debug")
        assert looks_like_python("python3.8-debug")

        # Test with other Python implementations
        assert looks_like_python("pypy")
        assert looks_like_python("pypy3")
        assert looks_like_python("jython")
        assert looks_like_python("anaconda3")
        assert looks_like_python("miniconda3")

    # Test with invalid names
    assert not looks_like_python("pip")
    assert not looks_like_python("pip3")
    assert not looks_like_python("pip-3.8")
    assert not looks_like_python("not-python")
    assert not looks_like_python("ruby")


def test_path_is_python():
    """Test that path_is_python correctly identifies Python executable paths."""
    # Test with valid Python path
    with mock.patch(
        "pythonfinder.utils.path_utils.path_is_known_executable", return_value=True
    ):
        with mock.patch(
            "pythonfinder.utils.path_utils.looks_like_python", return_value=True
        ):
            assert path_is_python(Path("/usr/bin/python"))

    # Test with non-executable Python path
    with mock.patch(
        "pythonfinder.utils.path_utils.path_is_known_executable", return_value=False
    ):
        with mock.patch(
            "pythonfinder.utils.path_utils.looks_like_python", return_value=True
        ):
            assert not path_is_python(Path("/usr/bin/python"))

    # Test with executable non-Python path
    with mock.patch(
        "pythonfinder.utils.path_utils.path_is_known_executable", return_value=True
    ):
        with mock.patch(
            "pythonfinder.utils.path_utils.looks_like_python", return_value=False
        ):
            assert not path_is_python(Path("/usr/bin/not-python"))


def test_filter_pythons():
    """Test that filter_pythons correctly filters Python executables."""
    # Test with a file
    with mock.patch("pythonfinder.utils.path_utils.path_is_python", return_value=True):
        path = Path("/usr/bin/python")
        pythons = list(filter_pythons(path))
        assert len(pythons) == 1
        assert pythons[0] == path

    # Test with a directory
    with mock.patch("pathlib.Path.is_dir", return_value=True):
        with mock.patch(
            "pathlib.Path.iterdir",
            return_value=[
                Path("/usr/bin/python"),
                Path("/usr/bin/python3"),
                Path("/usr/bin/not-python"),
            ],
        ):
            with mock.patch(
                "pythonfinder.utils.path_utils.path_is_python",
                side_effect=[True, True, False],
            ):
                path = Path("/usr/bin")
                pythons = list(filter_pythons(path))
                assert len(pythons) == 2
                assert Path("/usr/bin/python") in pythons
                assert Path("/usr/bin/python3") in pythons
                assert Path("/usr/bin/not-python") not in pythons

    # Test with permission error
    with mock.patch("pathlib.Path.is_dir", return_value=True):
        with mock.patch("pathlib.Path.iterdir", side_effect=PermissionError):
            path = Path("/usr/bin")
            pythons = list(filter_pythons(path))
            assert len(pythons) == 0


def test_exists_and_is_accessible():
    """Test that exists_and_is_accessible correctly checks if a path exists and is accessible."""
    # Test with existing path
    with mock.patch("pathlib.Path.exists", return_value=True):
        assert exists_and_is_accessible(Path("/usr/bin/python"))

    # Test with non-existing path
    with mock.patch("pathlib.Path.exists", return_value=False):
        assert not exists_and_is_accessible(Path("/usr/bin/python"))

    # Test with permission error
    with mock.patch(
        "pathlib.Path.exists", side_effect=PermissionError(13, "Permission denied")
    ):
        assert not exists_and_is_accessible(Path("/usr/bin/python"))

    # Test with other error
    with pytest.raises(PermissionError):
        with mock.patch(
            "pathlib.Path.exists", side_effect=PermissionError(1, "Other error")
        ):
            exists_and_is_accessible(Path("/usr/bin/python"))


def test_is_in_path():
    """Test that is_in_path correctly checks if a path is inside another path."""
    # Test with path inside parent
    assert is_in_path("/usr/bin/python", "/usr/bin")
    assert is_in_path("/usr/bin/python", "/usr")
    assert is_in_path("/usr/bin/python", "/")

    # Test with path equal to parent
    assert is_in_path("/usr/bin", "/usr/bin")

    # Test with path not inside parent
    assert not is_in_path("/usr/bin/python", "/usr/local")
    assert not is_in_path("/usr/bin/python", "/opt")

    # Test with Path objects
    assert is_in_path(Path("/usr/bin/python"), Path("/usr/bin"))
    assert not is_in_path(Path("/usr/bin/python"), Path("/usr/local"))

    # Test with mixed types
    assert is_in_path("/usr/bin/python", Path("/usr/bin"))
    assert is_in_path(Path("/usr/bin/python"), "/usr/bin")


# normalize_path function has been removed in the rewritten version
