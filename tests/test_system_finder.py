from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest import mock

from pythonfinder.finders.system_finder import SystemFinder


def test_system_finder_initialization():
    """Test that SystemFinder initializes with the correct parameters."""
    # Test with default parameters
    with mock.patch.dict(os.environ, {"PATH": ""}):
        with mock.patch(
            "pythonfinder.finders.system_finder.exists_and_is_accessible",
            return_value=False,
        ):
            finder = SystemFinder()
            assert finder.paths == []
            assert finder.only_python is False
            assert finder.ignore_unsupported is True

        # Test with custom parameters
        paths = [
            Path("/usr/bin"),
            Path("/usr/local/bin"),
        ]
        # Mock environment and accessibility for custom paths test
        with mock.patch.dict(os.environ, {"PATH": "", "VIRTUAL_ENV": ""}):
            with mock.patch(
                "pythonfinder.finders.system_finder.exists_and_is_accessible",
                return_value=True,
            ):
                finder = SystemFinder(
                    paths=paths,
                    global_search=False,
                    system=False,
                    only_python=True,
                    ignore_unsupported=False,
                )

                # Check that the paths were added correctly
                # On Windows, paths might have drive letters, so we need to normalize
                if os.name == "nt":
                    # Extract just the path part without drive letter for comparison
                    finder_paths = set(
                        p.as_posix().split(":", 1)[-1] for p in finder.paths
                    )
                    expected_paths = set(p.as_posix().split(":", 1)[-1] for p in paths)
                    assert finder_paths == expected_paths
                else:
                    assert set(p.as_posix() for p in finder.paths) == set(
                        p.as_posix() for p in paths
                    )
                assert finder.only_python is True
                assert finder.ignore_unsupported is False


def test_system_finder_with_global_search():
    """Test that SystemFinder correctly adds paths from PATH environment variable."""
    # Mock the PATH environment variable
    with mock.patch.dict(os.environ, {"PATH": "/usr/bin:/usr/local/bin"}):
        # Mock the exists_and_is_accessible function
        with mock.patch(
            "pythonfinder.finders.system_finder.exists_and_is_accessible",
            return_value=True,
        ):
            # Create a SystemFinder with global_search=True
            finder = SystemFinder(global_search=True)

            # Check that the paths from PATH were added using path normalization
            assert any("usr/bin" in p.as_posix() for p in finder.paths)
            assert any("usr/local/bin" in p.as_posix() for p in finder.paths)


def test_system_finder_with_system():
    """Test that SystemFinder correctly adds the system Python path."""
    # Mock the sys.executable
    with mock.patch.object(sys, "executable", "/usr/bin/python"):
        # Mock the exists_and_is_accessible function
        with mock.patch(
            "pythonfinder.finders.system_finder.exists_and_is_accessible",
            return_value=True,
        ):
            # Create a SystemFinder with system=True
            finder = SystemFinder(system=True)

            # Check that the system Python path was added using path normalization
            assert any("usr/bin" in p.as_posix() for p in finder.paths)


def test_system_finder_with_virtual_env():
    """Test that SystemFinder correctly adds the virtual environment path."""
    # Mock the VIRTUAL_ENV environment variable
    with mock.patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv", "PATH": ""}):
        # Mock the exists_and_is_accessible function and Path.exists
        with mock.patch(
            "pythonfinder.finders.system_finder.exists_and_is_accessible",
            return_value=True,
        ):
            with mock.patch("pathlib.Path.exists", return_value=True):
                # Create a SystemFinder with no global search or system paths
                finder = SystemFinder(global_search=False, system=False)

                # Check that the virtual environment path was added
                bin_dir = "Scripts" if os.name == "nt" else "bin"
                # Use path normalization for cross-platform compatibility
                assert any(
                    f"path/to/venv/{bin_dir}" in p.as_posix() for p in finder.paths
                )


def test_system_finder_with_custom_paths():
    """Test that SystemFinder correctly adds custom paths."""
    # Define custom paths
    custom_paths = [
        "/custom/path1",
        "/custom/path2",
        Path("/custom/path3"),
    ]

    # Mock the exists_and_is_accessible function
    with mock.patch(
        "pythonfinder.finders.system_finder.exists_and_is_accessible", return_value=True
    ):
        # Create a SystemFinder with custom paths
        finder = SystemFinder(paths=custom_paths)

        # Check that the custom paths were added using path normalization
        assert any("custom/path1" in p.as_posix() for p in finder.paths)
        assert any("custom/path2" in p.as_posix() for p in finder.paths)
        assert any("custom/path3" in p.as_posix() for p in finder.paths)


def test_system_finder_filters_non_existent_paths():
    """Test that SystemFinder filters out non-existent paths."""
    # Define paths
    paths = [
        "/existing/path1",
        "/non-existent/path",
        "/existing/path2",
    ]

    # Mock environment variables to avoid interference
    with mock.patch.dict(os.environ, {"PATH": "", "VIRTUAL_ENV": ""}):
        # Mock the exists_and_is_accessible function with specific return values for each path
        with mock.patch(
            "pythonfinder.finders.system_finder.exists_and_is_accessible"
        ) as mock_exists:
            # Set up the mock to return True for existing paths and False for non-existent path
            def side_effect(path):
                path_str = str(path)
                if "existing/path1" in path_str.replace("\\", "/"):
                    return True
                elif "non-existent/path" in path_str.replace("\\", "/"):
                    return False
                elif "existing/path2" in path_str.replace("\\", "/"):
                    return True
                return False

            mock_exists.side_effect = side_effect

            # Create a SystemFinder with the paths and no global search or system paths
            finder = SystemFinder(paths=paths, global_search=False, system=False)

            # Check that only the existing paths were added
            assert any(
                "existing/path1" in str(p).replace("\\", "/") for p in finder.paths
            )
            assert not any(
                "non-existent/path" in str(p).replace("\\", "/") for p in finder.paths
            )
            assert any(
                "existing/path2" in str(p).replace("\\", "/") for p in finder.paths
            )


def test_system_finder_inherits_from_path_finder():
    """Test that SystemFinder inherits from PathFinder."""
    # Create a SystemFinder
    finder = SystemFinder()

    # Check that it has the PathFinder methods
    assert hasattr(finder, "find_all_python_versions")
    assert hasattr(finder, "find_python_version")
    assert hasattr(finder, "which")

    # Mock the PathFinder methods
    with mock.patch(
        "pythonfinder.finders.path_finder.PathFinder.find_all_python_versions",
        return_value=["python1", "python2"],
    ):
        with mock.patch(
            "pythonfinder.finders.path_finder.PathFinder.find_python_version",
            return_value="python1",
        ):
            with mock.patch(
                "pythonfinder.finders.path_finder.PathFinder.which",
                return_value=Path("/usr/bin/python"),
            ):
                # Call the methods
                assert finder.find_all_python_versions() == ["python1", "python2"]
                assert finder.find_python_version() == "python1"
                assert finder.which("python") == Path("/usr/bin/python")
