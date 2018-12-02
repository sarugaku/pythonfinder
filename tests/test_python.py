# -*- coding=utf-8 -*-

import pythonfinder
import pytest
import os

from packaging.version import Version


def test_python_versions(monkeypatch, special_character_python):
    def mock_version(*args, **kwargs):
        version_output = "2.7.15+ (default, Jun 28 2018, 13:15:42)\n[GCC 7.2.0]"

        class FakeObj(object):
            def __init__(self, out):
                self.out = out

        c = FakeObj(version_output.split()[0])
        return c
    os.environ["PYTHONFINDER_IGNORE_UNSUPPORTED"] = str("1")
    monkeypatch.setattr("vistir.misc.run", mock_version)
    parsed = pythonfinder.models.python.PythonVersion.from_path(
        special_character_python.strpath
    )
    assert isinstance(parsed.version, Version)


@pytest.mark.parametrize(
    "path, version_output, version",
    [
        ("/fake/path/3.6.2/bin/python", "3.6.2 (default, Jun 28 2018, 13:15:42)", "3.6.2"),
        ("/fake/path/3.7.0/bin/python", "3.7.0 (default, Jun 28 2018, 13:15:42)", "3.7.0"),
        ("/fake/path/3.6.20/bin/python", "3.6.20 :: Continuum Analytics, Inc.", "3.6.20"),
        ("/fake/path/3.5.3/bin/python",
            "3.5.3 (fdd60ed87e941677e8ea11acf9f1819466521bf2, Apr 27 2018, 15:39:57)\n[PyPy 5.10.1 with GCC 4.2.1 Compatible Apple LLVM 9.0.0 (clang-900.0.39.2)]",
            "3.5.3",
        ),
        ("/fake/path/2.7.15+/bin/python", "2.7.15+ (default, Jun 28 2018, 13:15:42)", "2.7.15+")
    ],
)
def test_python_version_output_variants(
    monkeypatch, path, version_output, version
):
    def mock_version(*args, **kwargs):

        class FakeObj(object):
            def __init__(self, out):
                self.out = out

        c = FakeObj(version_output.split()[0])
        return c
    os.environ["PYTHONFINDER_IGNORE_UNSUPPORTED"] = str("1")
    monkeypatch.setattr("vistir.misc.run", mock_version)
    parsed = pythonfinder.models.python.PythonVersion.from_path(path)
    assert isinstance(parsed.version, Version)


def test_shims_are_removed(setup_pythons):
    from pythonfinder import Finder
    f = Finder(global_search=True, system=False, ignore_unsupported=True)
    python_versions = f.find_all_python_versions()
    anaconda = f.find_python_version("anaconda3-5.3.0")
    assert anaconda is not None, python_versions
    assert "shims" not in f.which("anaconda3-5.3.0")


def test_shims_are_kept(setup_pythons):
    del os.environ["PYENV_ROOT"]
    del os.environ["ASDF_DATA_DIR"]
    del os.environ["ASDF_DIR"]
    from pythonfinder import Finder
    f = Finder(global_search=True, system=False, ignore_unsupported=True)
    python_versions = f.find_all_python_versions()
    anaconda = f.find_python_version("anaconda3-5.3.0")
    assert anaconda is not None, python_versions
    assert "shims" in f.which("anaconda3-5.3.0")
