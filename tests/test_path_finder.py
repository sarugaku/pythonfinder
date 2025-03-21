from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from pythonfinder.finders.path_finder import PathFinder
from pythonfinder.models.python_info import PythonInfo


@pytest.fixture
def simple_path_finder():
    """Return a simple PathFinder instance with mocked paths."""
    paths = [
        Path("/usr/bin"),
        Path("/usr/local/bin"),
    ]
    return PathFinder(paths=paths)


def test_path_finder_initialization():
    """Test that PathFinder initializes with the correct parameters."""
    paths = [
        Path("/usr/bin"),
        Path("/usr/local/bin"),
    ]
    finder = PathFinder(paths=paths, only_python=True, ignore_unsupported=False)

    assert finder.paths == paths
    assert finder.only_python is True
    assert finder.ignore_unsupported is False
    assert finder._python_versions == {}


def test_create_python_info():
    """Test that _create_python_info correctly creates a PythonInfo object."""
    finder = PathFinder()

    # Test with valid Python path
    with mock.patch("pythonfinder.finders.path_finder.path_is_python", return_value=True):
        with mock.patch(
            "pythonfinder.finders.path_finder.get_python_version", return_value="3.8.0"
        ):
            with mock.patch(
                "pythonfinder.finders.path_finder.parse_python_version",
                return_value={
                    "major": 3,
                    "minor": 8,
                    "patch": 0,
                    "is_prerelease": False,
                    "is_postrelease": False,
                    "is_devrelease": False,
                    "is_debug": False,
                    "version": "3.8.0",
                },
            ):
                with mock.patch(
                    "pythonfinder.finders.path_finder.guess_company",
                    return_value="PythonCore",
                ):
                    python_info = finder._create_python_info(Path("/usr/bin/python"))

                    assert python_info is not None
                    assert python_info.path == Path("/usr/bin/python")
                    assert python_info.version_str == "3.8.0"
                    assert python_info.major == 3
                    assert python_info.minor == 8
                    assert python_info.patch == 0
                    assert python_info.is_prerelease is False
                    assert python_info.is_postrelease is False
                    assert python_info.is_devrelease is False
                    assert python_info.is_debug is False
                    assert python_info.company == "PythonCore"
                    assert python_info.name == "python"
                    # Handle Windows path separators in the executable path
                    if os.name == "nt":
                        assert (
                            python_info.executable.replace("\\", "/") == "/usr/bin/python"
                        )
                    else:
                        assert python_info.executable == "/usr/bin/python"

    # Test with non-Python path
    with mock.patch(
        "pythonfinder.finders.path_finder.path_is_python", return_value=False
    ):
        python_info = finder._create_python_info(Path("/usr/bin/not-python"))
        assert python_info is None

    # Test with invalid Python version
    with mock.patch("pythonfinder.finders.path_finder.path_is_python", return_value=True):
        # With ignore_unsupported=True
        finder = PathFinder(ignore_unsupported=True)
        with mock.patch(
            "pythonfinder.finders.path_finder.get_python_version",
            side_effect=Exception("Test exception"),
        ):
            python_info = finder._create_python_info(Path("/usr/bin/python"))
            assert python_info is None

        # With ignore_unsupported=False
        finder = PathFinder(ignore_unsupported=False)
        with mock.patch(
            "pythonfinder.finders.path_finder.get_python_version",
            side_effect=Exception("Test exception"),
        ):
            with pytest.raises(Exception, match="Test exception"):
                finder._create_python_info(Path("/usr/bin/python"))


def test_iter_pythons(simple_path_finder):
    """Test that _iter_pythons correctly iterates over Python executables."""
    # Mock the paths
    path1 = Path("/usr/bin/python")
    path2 = Path("/usr/bin/python3")
    path3 = Path("/usr/local/bin/python")

    # Mock the PythonInfo objects
    python_info1 = PythonInfo(
        path=path1,
        version_str="2.7.0",
        major=2,
        minor=7,
        patch=0,
    )
    python_info2 = PythonInfo(
        path=path2,
        version_str="3.8.0",
        major=3,
        minor=8,
        patch=0,
    )
    python_info3 = PythonInfo(
        path=path3,
        version_str="3.9.0",
        major=3,
        minor=9,
        patch=0,
    )

    # Mock the _create_python_info method
    with mock.patch.object(
        simple_path_finder,
        "_create_python_info",
        side_effect=[python_info1, python_info2, python_info3],
    ):
        # Mock the path_is_python function
        with mock.patch(
            "pythonfinder.finders.path_finder.path_is_python", return_value=True
        ):
            # Mock the filter_pythons function
            with mock.patch(
                "pythonfinder.finders.path_finder.filter_pythons",
                side_effect=[[path1, path2], [path3]],
            ):
                # Mock the Path.exists and Path.is_file methods
                with mock.patch("pathlib.Path.exists", return_value=True):
                    with mock.patch("pathlib.Path.is_dir", return_value=True):
                        # Get all Python versions
                        pythons = list(simple_path_finder._iter_pythons())

                        # Check that we got all three Python versions
                        assert len(pythons) == 3
                        assert python_info1 in pythons
                        assert python_info2 in pythons
                        assert python_info3 in pythons

                        # Check that the Python versions were cached
                        assert path1 in simple_path_finder._python_versions
                        assert path2 in simple_path_finder._python_versions
                        assert path3 in simple_path_finder._python_versions
                        assert simple_path_finder._python_versions[path1] == python_info1
                        assert simple_path_finder._python_versions[path2] == python_info2
                        assert simple_path_finder._python_versions[path3] == python_info3


def test_find_all_python_versions(simple_path_finder):
    """Test that find_all_python_versions correctly finds all Python versions."""
    # Mock the PythonInfo objects
    python_info1 = PythonInfo(
        path=Path("/usr/bin/python"),
        version_str="2.7.0",
        major=2,
        minor=7,
        patch=0,
    )
    python_info2 = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
        minor=8,
        patch=0,
    )
    python_info3 = PythonInfo(
        path=Path("/usr/local/bin/python"),
        version_str="3.9.0",
        major=3,
        minor=9,
        patch=0,
    )

    # Mock the _iter_pythons method
    with mock.patch.object(
        simple_path_finder,
        "_iter_pythons",
        return_value=[python_info1, python_info2, python_info3],
    ):
        # Find all Python versions
        pythons = simple_path_finder.find_all_python_versions()

        # Check that we got all three Python versions
        assert len(pythons) == 3
        assert python_info1 in pythons
        assert python_info2 in pythons
        assert python_info3 in pythons

        # Check that the versions are sorted correctly (highest version first)
        assert pythons[0] == python_info3  # 3.9.0
        assert pythons[1] == python_info2  # 3.8.0
        assert pythons[2] == python_info1  # 2.7.0

        # Find Python versions with specific criteria
        pythons = simple_path_finder.find_all_python_versions(major=3)
        assert len(pythons) == 2
        assert python_info2 in pythons
        assert python_info3 in pythons

        pythons = simple_path_finder.find_all_python_versions(major=3, minor=8)
        assert len(pythons) == 1
        assert pythons[0] == python_info2

        pythons = simple_path_finder.find_all_python_versions(major=2, minor=7, patch=0)
        assert len(pythons) == 1
        assert pythons[0] == python_info1

        # Find Python versions with non-matching criteria
        pythons = simple_path_finder.find_all_python_versions(major=4)
        assert len(pythons) == 0


def test_find_python_version(simple_path_finder):
    """Test that find_python_version correctly finds a Python version."""
    # Mock the find_all_python_versions method
    python_info = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
        minor=8,
        patch=0,
    )

    with mock.patch.object(
        simple_path_finder, "find_all_python_versions", return_value=[python_info]
    ):
        # Find a Python version
        result = simple_path_finder.find_python_version(major=3, minor=8)

        # Check that we got the correct Python version
        assert result == python_info

        # Check that find_all_python_versions was called with the correct parameters
        simple_path_finder.find_all_python_versions.assert_called_once_with(
            3, 8, None, None, None, None, None
        )

    # Test with no matching Python versions
    with mock.patch.object(
        simple_path_finder, "find_all_python_versions", return_value=[]
    ):
        result = simple_path_finder.find_python_version(major=4)
        assert result is None


def test_which(simple_path_finder):
    """Test that which correctly finds an executable."""
    # Test with only_python=False
    simple_path_finder.only_python = False

    # Mock the Path.exists and Path.is_dir methods
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.is_dir", return_value=True):
            # Mock the os.access method
            with mock.patch("os.access", return_value=True):
                # Find an executable
                result = simple_path_finder.which("python")

                # Check that we got the correct path
                if os.name == "nt":
                    # On Windows, normalize the path for comparison
                    assert result.as_posix().endswith(
                        "/usr/bin/python"
                    ) or result.as_posix().endswith("/usr/bin/python.exe")
                else:
                    assert result == Path("/usr/bin/python")

    # Test with only_python=True and python executable
    simple_path_finder.only_python = True

    # Mock the Path.exists and Path.is_dir methods
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.is_dir", return_value=True):
            # Mock the os.access method
            with mock.patch("os.access", return_value=True):
                # Find an executable
                result = simple_path_finder.which("python")

                # Check that we got the correct path
                if os.name == "nt":
                    # On Windows, normalize the path for comparison
                    assert result.as_posix().endswith(
                        "/usr/bin/python"
                    ) or result.as_posix().endswith("/usr/bin/python.exe")
                else:
                    assert result == Path("/usr/bin/python")

    # Test with only_python=True and non-python executable
    simple_path_finder.only_python = True

    # Find an executable
    result = simple_path_finder.which("pip")

    # Check that we got None
    assert result is None

    # Test with non-existent executable
    simple_path_finder.only_python = False

    # Mock the Path.exists and Path.is_dir methods
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.is_dir", return_value=True):
            # Mock the os.access method
            with mock.patch("os.access", return_value=False):
                # Find an executable
                result = simple_path_finder.which("python")

                # Check that we got None
                assert result is None

    # Test with Windows-specific behavior
    if os.name == "nt":
        simple_path_finder.only_python = False

        # Mock the Path.exists and Path.is_dir methods
        with mock.patch("pathlib.Path.exists", return_value=True):
            with mock.patch("pathlib.Path.is_dir", return_value=True):
                # Mock the os.access method
                with mock.patch("os.access", return_value=True):
                    # Find an executable without .exe extension
                    result = simple_path_finder.which("python")

                    # Check that we got the correct path with .exe extension
                    assert result == Path("/usr/bin/python.exe")
