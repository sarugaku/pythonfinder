# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function

import os
import sys

import pytest
import six
import vistir
from packaging.version import Version

import pythonfinder

from .testutils import is_in_ospath, normalized_match, print_python_versions


def test_python_versions(monkeypatch, special_character_python):
    def mock_version(*args, **kwargs):
        version_output = "2.7.15+ (default, Jun 28 2018, 13:15:42)\n[GCC 7.2.0]"

        class FakeObj(object):
            def __init__(self, out):
                self.out = out

        c = FakeObj(version_output.split()[0])
        return c

    os.environ["PYTHONFINDER_IGNORE_UNSUPPORTED"] = str("1")
    with monkeypatch.context() as m:
        m.setattr("vistir.misc.run", mock_version)
        parsed = pythonfinder.models.python.PythonVersion.from_path(
            special_character_python.strpath
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
            "2.7.15+",
        ),
    ],
)
def test_python_version_output_variants(monkeypatch, path, version_output, version):
    def mock_version(*args, **kwargs):
        class FakeObj(object):
            def __init__(self, out):
                self.out = out

        c = FakeObj(version_output.split()[0])
        return c

    with monkeypatch.context() as m:
        os.environ["PYTHONFINDER_IGNORE_UNSUPPORTED"] = str("1")
        m.setattr("vistir.misc.run", mock_version)
        parsed = pythonfinder.models.python.PythonVersion.from_path(path)
        assert isinstance(parsed.version, Version)


def test_shims_are_kept(monkeypatch, no_pyenv_root_envvar, setup_pythons, no_virtual_env):
    with monkeypatch.context() as m:
        # pyenv_dir = pythonfinder.utils.normalize_path("./.pyenv")
        # asdf_dir = pythonfinder.utils.normalize_path("./.asdf")
        # m.delenv("PYENV_ROOT")
        # m.delenv("ASDF_DATA_DIR")
        # six.moves.reload_module(pythonfinder.environment)
        # six.moves.reload_module(pythonfinder.models.path)
        # m.setattr(pythonfinder.environment, "PYENV_INSTALLED", False)
        # m.setattr(pythonfinder.environment, "ASDF_INSTALLED", False)
        # m.setattr(pythonfinder.environment, "PYENV_ROOT", pyenv_dir)
        # m.setattr(pythonfinder.environment, "ASDF_DATA_DIR", asdf_dir)
        # m.setattr(
        #     pythonfinder.environment,
        #     "SHIM_PATHS",
        #     pythonfinder.environment.get_shim_paths(),
        # )
        # if "VIRTUAL_ENV" in os.environ:
        #     os_path = os.environ["PATH"].split(os.pathsep)
        #     env_path = next(
        #         iter(
        #             [
        #                 p
        #                 for p in os_path
        #                 if pythonfinder.utils.is_in_path(p, os.environ["VIRTUAL_ENV"])
        #             ]
        #         ),
        #         None,
        #     )
        #     if env_path is not None:
        #         os_path.remove(env_path)
        #         os.environ["PATH"] = os.pathsep.join(os_path)
        #     del os.environ["VIRTUAL_ENV"]
        f = pythonfinder.pythonfinder.Finder(
            global_search=True, system=False, ignore_unsupported=True
        )
        f.rehash()
        assert pythonfinder.environment.get_shim_paths() == []
        assert is_in_ospath("./.asdf/shims")
        assert not f.system_path.finders
        assert (
            os.path.join(vistir.path.normalize_path("./.asdf/shims"))
            in f.system_path.path_order
        )
        python_versions = f.find_all_python_versions()
        anaconda = f.find_python_version("anaconda3-5.3.0")
        if not anaconda:
            print("OS PATH: {0}".format(os.environ["PATH"]), file=sys.stderr)
            print("PYENV DIR:")
            for fn in os.listdir(vistir.path.normalize_path("./.asdf/shims")):
                print("    {0}".format(fn), file=sys.stderr)
            print_python_versions(python_versions)
            print(
                "Finder path order: {0}".format(f.system_path.path_order), file=sys.stderr
            )
        assert anaconda is not None, python_versions
        assert "shims" in anaconda.path.as_posix(), [
            f.system_path.path_order,
            f.system_path.asdf_finder.roots,
        ]
        assert "shims" in f.which("anaconda3-5.3.0").path.as_posix()


def test_shims_are_removed(monkeypatch, no_virtual_env, setup_pythons):
    with monkeypatch.context() as m:
        pyenv_dir = pythonfinder.utils.normalize_path("./.pyenv")
        asdf_dir = pythonfinder.utils.normalize_path("./.asdf")
        six.moves.reload_module(pythonfinder.environment)
        six.moves.reload_module(pythonfinder.models.path)
        m.setattr(
            pythonfinder.environment,
            "SHIM_PATHS",
            pythonfinder.environment.get_shim_paths(),
        )
        f = pythonfinder.pythonfinder.Finder(
            global_search=True, system=False, ignore_unsupported=True
        )
        f.rehash()
        # assert "pyenv" in f.system_path.finders
        python_versions = f.find_all_python_versions()
        assert os.environ["PYENV_ROOT"] == os.path.abspath(
            os.path.join(os.curdir, ".pyenv")
        )
        assert os.environ["PYENV_ROOT"] == pythonfinder.environment.PYENV_ROOT
        assert pythonfinder.environment.PYENV_INSTALLED
        assert f.system_path.pyenv_finder is not None
        # assert len(python_versions) == 0
        python_version_paths = list(
            v.path
            for v in python_versions
            if normalized_match(str(v.path), os.environ["PYENV_ROOT"])
        )
        # Make sure we have an entry for every python version installed
        python_names = set(list(v.parent.parent.name for v in python_version_paths))
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
        assert "shims" not in which_anaconda.path.as_posix()


# @pytest.mark.skipif(os.name != "nt", "windows only test")
def test_windows_pythonfinder(expected_python_versions, all_python_versions):
    assert sorted(expected_python_versions) == sorted(all_python_versions)
