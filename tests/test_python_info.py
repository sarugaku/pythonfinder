from __future__ import annotations

from pathlib import Path

from packaging.version import Version

from pythonfinder.models.python_info import PythonInfo


def test_python_info_initialization():
    """Test that PythonInfo initializes with the correct parameters."""
    python_info = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
        minor=8,
        patch=0,
        is_prerelease=False,
        is_postrelease=False,
        is_devrelease=False,
        is_debug=False,
        version=Version("3.8.0"),
        architecture="64bit",
        company="PythonCore",
        name="python3.8",
        executable="/usr/bin/python3",
    )

    assert python_info.path == Path("/usr/bin/python3")
    assert python_info.version_str == "3.8.0"
    assert python_info.major == 3
    assert python_info.minor == 8
    assert python_info.patch == 0
    assert python_info.is_prerelease is False
    assert python_info.is_postrelease is False
    assert python_info.is_devrelease is False
    assert python_info.is_debug is False
    assert python_info.version == Version("3.8.0")
    assert python_info.architecture == "64bit"
    assert python_info.company == "PythonCore"
    assert python_info.name == "python3.8"
    assert python_info.executable == "/usr/bin/python3"


def test_python_info_version_tuple():
    """Test the version_tuple property."""
    python_info = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
        minor=8,
        patch=0,
        is_prerelease=True,
        is_devrelease=False,
        is_debug=True,
    )

    expected_tuple = (3, 8, 0, True, False, True)
    assert python_info.version_tuple == expected_tuple


def test_python_info_version_sort():
    """Test the version_sort property."""
    # PythonCore company
    python_info1 = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
        minor=8,
        patch=0,
        company="PythonCore",
    )

    # Non-PythonCore company
    python_info2 = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
        minor=8,
        patch=0,
        company="Anaconda",
    )

    # Pre-release
    python_info3 = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0a1",
        major=3,
        minor=8,
        patch=0,
        is_prerelease=True,
    )

    # Post-release
    python_info4 = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0.post1",
        major=3,
        minor=8,
        patch=0,
        is_postrelease=True,
    )

    # Dev-release
    python_info5 = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0.dev1",
        major=3,
        minor=8,
        patch=0,
        is_devrelease=True,
    )

    # Debug
    python_info6 = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0-debug",
        major=3,
        minor=8,
        patch=0,
        is_debug=True,
    )

    # Different versions
    python_info7 = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.9.0",
        major=3,
        minor=9,
        patch=0,
    )

    python_info8 = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.1",
        major=3,
        minor=8,
        patch=1,
    )

    # Check individual sort tuples
    assert python_info1.version_sort == (1, 3, 8, 0, 2)  # PythonCore
    assert python_info2.version_sort == (0, 3, 8, 0, 2)  # Non-PythonCore
    assert python_info3.version_sort == (0, 3, 8, 0, 1)  # Pre-release
    assert python_info4.version_sort == (0, 3, 8, 0, 3)  # Post-release
    assert python_info5.version_sort == (0, 3, 8, 0, 0)  # Dev-release
    assert python_info6.version_sort == (0, 3, 8, 0, 1)  # Debug
    assert python_info7.version_sort == (0, 3, 9, 0, 2)  # Higher minor
    assert python_info8.version_sort == (0, 3, 8, 1, 2)  # Higher patch

    # Test sorting
    versions = [
        python_info1,
        python_info2,
        python_info3,
        python_info4,
        python_info5,
        python_info6,
        python_info7,
        python_info8,
    ]

    sorted_versions = sorted(versions, key=lambda x: x.version_sort, reverse=True)

    # Expected order (highest to lowest):
    # 1. python_info7 (3.9.0)
    # 2. python_info4 (3.8.0.post1)
    # 3. python_info8 (3.8.1)
    # 4. python_info1 (3.8.0 PythonCore)
    # 5. python_info2 (3.8.0 Anaconda)
    # 6. python_info3 (3.8.0a1) or python_info6 (3.8.0-debug)
    # 7. python_info6 (3.8.0-debug) or python_info3 (3.8.0a1)
    # 8. python_info5 (3.8.0.dev1)

    assert sorted_versions[0] == python_info7
    assert sorted_versions[1] == python_info4
    assert sorted_versions[2] == python_info8
    assert sorted_versions[3] == python_info1
    assert sorted_versions[4] == python_info2
    assert sorted_versions[7] == python_info5  # Dev release is always last


def test_python_info_matches():
    """Test the matches method."""
    python_info = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
        minor=8,
        patch=0,
        is_prerelease=False,
        is_devrelease=False,
        is_debug=False,
        architecture="64bit",
        name="python3.8",
    )

    # Test matching with exact version
    assert python_info.matches(major=3, minor=8, patch=0)

    # Test matching with partial version
    assert python_info.matches(major=3, minor=8)
    assert python_info.matches(major=3)

    # Test matching with architecture
    assert python_info.matches(arch="64bit")
    assert python_info.matches(arch="64")  # Should convert to 64bit

    # Test matching with name
    assert python_info.matches(python_name="python3.8")
    assert python_info.matches(python_name="python3")  # Partial match

    # Test non-matching
    assert not python_info.matches(major=2)
    assert not python_info.matches(minor=7)
    assert not python_info.matches(patch=1)
    assert not python_info.matches(pre=True)
    assert not python_info.matches(dev=True)
    assert not python_info.matches(debug=True)
    assert not python_info.matches(arch="32bit")
    assert not python_info.matches(python_name="python2")


def test_python_info_as_dict():
    """Test the as_dict method."""
    python_info = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
        minor=8,
        patch=0,
        is_prerelease=True,
        is_postrelease=True,
        is_devrelease=True,
        is_debug=True,
        version=Version("3.8.0"),
        company="PythonCore",
    )

    expected_dict = {
        "major": 3,
        "minor": 8,
        "patch": 0,
        "is_prerelease": True,
        "is_postrelease": True,
        "is_devrelease": True,
        "is_debug": True,
        "version": Version("3.8.0"),
        "company": "PythonCore",
    }

    assert python_info.as_dict() == expected_dict


def test_python_info_get_architecture():
    """Test the _get_architecture method."""
    # Test with architecture already set
    python_info = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
        architecture="64bit",
    )

    assert python_info._get_architecture() == "64bit"

    # Test with path but no architecture (would use platform.architecture in real code)
    # This is hard to test without mocking platform.architecture, so we'll just
    # check that it doesn't raise an exception
    python_info = PythonInfo(
        path=Path("/usr/bin/python3"),
        version_str="3.8.0",
        major=3,
    )

    arch = python_info._get_architecture()
    assert isinstance(arch, str)
    assert arch in ("32bit", "64bit")
