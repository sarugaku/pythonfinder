# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function

import functools
import importlib
import os
import sys

import pytest
from packaging.version import Version

import pythonfinder

from .testutils import (
    is_in_ospath,
    normalize_path,
    normalized_match,
    print_python_versions,
)


@pytest.mark.skipif(sys.version_info < (3,), reason="Must run on Python 3")
def test_python_versions(monkeypatch, special_character_python):
    def mock_version(*args, **kwargs):
        version_output = "2.7.15+ (default, Jun 28 2018, 13:15:42)\n[GCC 7.2.0]"

        class FakeObj(object):
            def __init__(self, out):
                self.out = out

            def communicate(self):
                return self.out, ""

            def kill(self):
                pass

        c = FakeObj(version_output.split()[0])
        return c

    os.environ["PYTHONFINDER_IGNORE_UNSUPPORTED"] = str("1")
    with monkeypatch.context() as m:
        m.setattr("subprocess.Popen", mock_version)
        parsed = pythonfinder.models.python.PythonVersion.from_path(
            special_character_python.as_posix()
        )
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
        class FakeObj(object):
            def __init__(self, out):
                self.out = out

            def communicate(self):
                return self.out, ""

            def kill(self):
                pass

        c = FakeObj(".".join([str(i) for i in version_output.split()[0].split(".")]))
        return c

    def get_python_version(path, orig_fn=None):
        if not os.path.exists(path):
            return mock_version(version_output)
        return orig_fn(path)

    with monkeypatch.context() as m:
        os.environ["PYTHONFINDER_IGNORE_UNSUPPORTED"] = str("1")
        m.setattr("subprocess.Popen", mock_version)
        orig_run_fn = pythonfinder.utils.get_python_version
        get_pyversion = functools.partial(get_python_version, orig_fn=orig_run_fn)
        m.setattr("pythonfinder.utils.get_python_version", get_pyversion)
        # m.setattr("pythonfinder.utils.get_python_version", mock_version)
        parsed = pythonfinder.models.python.PythonVersion.from_path(path)
        assert isinstance(parsed.version, Version)


@pytest.mark.skip_nt
def test_shims_are_kept(monkeypatch, no_pyenv_root_envvar, setup_pythons, no_virtual_env):
    with monkeypatch.context() as m:
        os.environ["PATH"] = "{0}:{1}".format(
            normalize_path("~/.pyenv/shims"), os.environ["PATH"]
        )
        f = pythonfinder.pythonfinder.Finder(
            global_search=True, system=False, ignore_unsupported=True
        )
        f.rehash()
        # assert pythonfinder.environment.get_shim_paths() == []
        assert is_in_ospath("~/.pyenv/shims")
        shim_paths = pythonfinder.environment.get_shim_paths()
        # Shims directories are no longer added to the system path order
        # but instead are used as indicators of the presence of the plugin
        # and used to trigger plugin setup -- this is true only if ``PYENV_ROOT`` is set`
        if shim_paths:
            assert (
                os.path.join(normalize_path("~/.pyenv/shims"))
                not in f.system_path.path_order
            ), (
                pythonfinder.environment.get_shim_paths()
            )  # "\n".join(f.system_path.path_order)
        else:
            assert (
                os.path.join(normalize_path("~/.pyenv/shims")) in f.system_path.path_order
            ), "\n".join(f.system_path.path_order)
        python_versions = f.find_all_python_versions()
        anaconda = f.find_python_version("anaconda3-5.3.0")
        assert anaconda is not None, python_versions
        assert "shims" in anaconda.path.as_posix(), [
            f.system_path.path_order,
            f.system_path.pyenv_finder.roots,
        ]
        # for docker, use just 'anaconda'
        for path in f.system_path.path_order:
            print(
                "path: {0}    Entry: {1}".format(path, f.system_path.get_path(path)),
                file=sys.stderr,
            )
        which_anaconda = f.which("anaconda3-5.3.0")
        if shim_paths:
            assert "shims" not in which_anaconda.path.as_posix()
        else:
            assert "shims" in which_anaconda.path.as_posix()


@pytest.mark.skip_nt
def test_shims_are_removed(monkeypatch, no_virtual_env, setup_pythons):
    with monkeypatch.context() as m:
        pyenv_dir = pythonfinder.utils.normalize_path("~/.pyenv")
        asdf_dir = pythonfinder.utils.normalize_path("~/.asdf")
        importlib.reload(pythonfinder.environment)
        importlib.reload(pythonfinder.models.path)
        m.setattr(
            pythonfinder.environment,
            "SHIM_PATHS",
            pythonfinder.environment.get_shim_paths(),
        )
        f = pythonfinder.pythonfinder.Finder(
            global_search=True, system=False, ignore_unsupported=True
        )
        f.rehash()
        python_versions = f.find_all_python_versions()
        assert os.environ["PYENV_ROOT"] == os.path.abspath(
            os.path.join(os.path.expanduser("~"), ".pyenv")
        )
        assert os.environ["PYENV_ROOT"] == pythonfinder.environment.PYENV_ROOT
        assert pythonfinder.environment.PYENV_INSTALLED
        assert f.system_path.pyenv_finder is not None
        python_version_paths = list(
            v.path
            for v in python_versions
            if normalized_match(str(v.path), os.environ["PYENV_ROOT"])
        )
        # Make sure we have an entry for every python version installed
        python_names = set(list(v.parent.parent.name for v in python_version_paths))
        # this is how we test in docker / on local machines with python installs
        # setup_pythons = {version.name for version in all_python_versions if any(plugin in version.path for plugin in ("pyenv", "asdf"))}
        # this is the test implementation when we are simulating
        setup_key_list = [
            set(list(finder.keys())) for finder in list(setup_pythons.values())
        ]
        setup_pythons = {python for finder in setup_key_list for python in finder}
        # this calculates the pythons not present when we ran `find_all_python_versions`
        missing_from_finder = python_names ^ setup_pythons
        if missing_from_finder:
            print_python_versions(python_versions)
            for p in python_version_paths:
                print("path: {0}".format(p), file=sys.stderr)
            for p in sorted(python_names):
                print("python_name: {0}".format(p), file=sys.stderr)
            for p in sorted(list(setup_pythons)):
                print("setup python key: {0}".format(p), file=sys.stderr)
        assert not missing_from_finder, missing_from_finder
        anaconda = f.find_python_version("anaconda3-5.3.0")
        assert anaconda is not None, os.listdir(
            os.path.join(pyenv_dir, "versions", "anaconda3-5.3.0", "bin")
        )
        assert "shims" not in anaconda.path.as_posix()
        which_anaconda = f.which("anaconda3-5.3.0")
        # for docker, use just 'anaconda'
        # which_anaconda = f.which("anaconda")
        assert "shims" not in which_anaconda.path.as_posix()


@pytest.mark.skip_nt
def test_pythonfinder(expected_python_versions, all_python_versions):
    assert sorted(expected_python_versions) == sorted(all_python_versions)
