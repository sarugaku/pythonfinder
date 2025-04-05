from __future__ import annotations

import functools
import os
import sys

import pytest
from packaging.version import Version

from pythonfinder import utils
from pythonfinder.models.python_info import PythonInfo
from pythonfinder.pythonfinder import Finder


@pytest.mark.skipif(sys.version_info < (3,), reason="Must run on Python 3")
def test_python_versions(monkeypatch, special_character_python):
    def mock_version(*args, **kwargs):
        version_output = "2.7.15+ (default, Jun 28 2018, 13:15:42)\n[GCC 7.2.0]"

        class FakeObj:
            def __init__(self, out):
                self.out = out
                self.args = ['py', '--list-paths']

            def communicate(self, *args, **kwargs):
                return self.out, ""

            def kill(self):
                pass
                
            def __enter__(self):
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.kill()
                
            def poll(self):
                return 0

        c = FakeObj(version_output.split()[0])
        return c

    os.environ["PYTHONFINDER_IGNORE_UNSUPPORTED"] = "1"
    with monkeypatch.context() as m:
        m.setattr("subprocess.Popen", mock_version)
        path = special_character_python.as_posix()
        finder = Finder(path=path)
        parsed = finder.find_python_version()
        assert isinstance(parsed.version, Version)


@pytest.mark.parametrize(
    "path, version_output, version",
    [
        (
            "/fake/path/3.6.2/bin/python",
            "3.6.2 (default, Jun 28 2018, 13:15:42)",
            "3.6.2",
        ),
        (
            "/fake/path/3.7.0/bin/python",
            "3.7.0 (default, Jun 28 2018, 13:15:42)",
            "3.7.0",
        ),
        ("/fake/path/3.6.20/bin/python", "3.6.20 :: Continuum Analytics, Inc.", "3.6.20"),
        (
            "/fake/path/3.5.3/bin/python",
            "3.5.3 (fdd60ed87e941677e8ea11acf9f1819466521bf2, Apr 27 2018, 15:39:57)\n[PyPy 5.10.1 with GCC 4.2.1 Compatible Apple LLVM 9.0.0 (clang-900.0.39.2)]",
            "3.5.3",
        ),
        (
            "/fake/path/2.7.15+/bin/python",
            "2.7.15+ (default, Jun 28 2018, 13:15:42)",
            "2.7.15",
        ),
    ],
)
def test_python_version_output_variants(monkeypatch, path, version_output, version):
    def mock_version(*args, **kwargs):
        class FakeObj:
            def __init__(self, out):
                self.out = out
                self.args = ['py', '--list-paths']

            def communicate(self, *args, **kwargs):
                return self.out, ""

            def kill(self):
                pass
                
            def __enter__(self):
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.kill()
                
            def poll(self):
                return 0

        c = FakeObj(".".join([str(i) for i in version_output.split()[0].split(".")]))
        return c

    def get_python_version(path, orig_fn=None):
        if not os.path.exists(path):
            return mock_version(version_output)
        return orig_fn(path)

    with monkeypatch.context() as m:
        os.environ["PYTHONFINDER_IGNORE_UNSUPPORTED"] = "1"
        m.setattr("subprocess.Popen", mock_version)
        orig_run_fn = utils.get_python_version
        get_pyversion = functools.partial(get_python_version, orig_fn=orig_run_fn)
        m.setattr("pythonfinder.utils.get_python_version", get_pyversion)

        # Create a PythonInfo object directly instead of using PythonVersion.from_path
        from pathlib import Path

        from pythonfinder.utils.version_utils import parse_python_version

        path_obj = Path(path)
        version_data = parse_python_version(version_output.split()[0])
        python_info = PythonInfo(
            path=path_obj,
            version_str=version_output.split()[0],
            major=version_data["major"],
            minor=version_data["minor"],
            patch=version_data["patch"],
            is_prerelease=version_data["is_prerelease"],
            is_postrelease=version_data["is_postrelease"],
            is_devrelease=version_data["is_devrelease"],
            is_debug=version_data["is_debug"],
            version=version_data["version"],
        )

        assert isinstance(python_info.version, Version)


@pytest.mark.skipif(os.name == "nt", reason="Does not run on Windows")
def test_pythonfinder(expected_python_versions, all_python_versions):
    # Sort by version_sort property instead of using the < operator directly
    sorted_expected = sorted(expected_python_versions, key=lambda x: (x.version, x.path))
    sorted_actual = sorted(all_python_versions, key=lambda x: (x.version, x.path))
    assert sorted_expected == sorted_actual
