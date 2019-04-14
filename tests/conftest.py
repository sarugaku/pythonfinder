# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function

import itertools
import os
import random
import sys
from collections import namedtuple

import click
import click.testing
import pytest
import vistir

import pythonfinder

pythoninfo = namedtuple("PythonVersion", ["version", "path", "arch"])

# def pytest_generate_tests(metafunc):
#     idlist = []
#     argvalues = []
#     for python in PYTHON_VERSIONS:
#         idlist.append(python.path.as_posix())
#         argnames = ["python",]
#         argvalues.append(([python,]))
#     metafunc.parametrize(argnames, argvalues, ids=idlist, scope="function")


# @pytest.fixture(params=PYTHON_VERSIONS)
# def python(request):
#     return request.params


STACKLESS = [
    "stackless-2.7-dev",
    "stackless-2.7.2",
    "stackless-2.7.3",
    "stackless-2.7.4",
    "stackless-2.7.5",
    "stackless-2.7.6",
    "stackless-2.7.7",
    "stackless-2.7.8",
    "stackless-2.7.9",
    "stackless-2.7.10",
    "stackless-2.7.11",
    "stackless-2.7.12",
    "stackless-2.7.14",
    "stackless-3.2.2",
    "stackless-3.2.5",
    "stackless-3.3.5",
    "stackless-3.3.7",
    "stackless-3.4-dev",
    "stackless-3.4.1",
    "stackless-3.4.2",
    "stackless-3.4.7",
    "stackless-3.5.4",
]
PYPY = [
    "pypy3-2.3.1",
    "pypy3-2.4.0-src",
    "pypy3-2.4.0",
    "pypy2-5.6.0",
    "pypy2.7-5.10.0",
    "pypy2.7-6.0.0",
    "pypy-5.3.1",
    "pypy3.5-5.10.1",
    "pypy3.5-6.0.0-src",
    "pypy3.5-6.0.0",
]
PYSTON = ["pyston-0.5.1", "pyston-0.6.0", "pyston-0.6.1"]
MINICONDA = [
    "miniconda-2.2.2",
    "miniconda-3.0.0",
    "miniconda-3.0.4",
    "miniconda-3.0.5",
    "miniconda-3.3.0",
    "miniconda-3.4.2",
    "miniconda3-3.18.3",
    "miniconda3-3.19.0",
    "miniconda3-4.0.5",
    "miniconda3-4.1.11",
    "miniconda3-4.3.27",
    "miniconda3-4.3.30",
]
MICROPYTHON = ["micropython-1.9.3", "micropython-1.9.4"]
JYTHON = [
    "jython-2.5-dev",
    "jython-2.5.1",
    "jython-2.5.2",
    "jython-2.5.3",
    "jython-2.5.4-rc1",
    "jython-2.7.0",
    "jython-2.7.1",
]
ANACONDA = [
    "anaconda2-2.4.1",
    "anaconda2-2.5.0",
    "anaconda2-4.0.0",
    "anaconda2-4.1.0",
    "anaconda2-4.1.1",
    "anaconda2-4.2.0",
    "anaconda2-4.3.0",
    "anaconda2-4.3.1",
    "anaconda2-4.4.0",
    "anaconda3-4.1.1",
    "anaconda3-4.2.0",
    "anaconda3-4.3.0",
    "anaconda3-4.3.1",
    "anaconda3-4.4.0",
    "anaconda3-5.0.0",
    "anaconda3-5.0.1",
    "anaconda3-5.1.0",
    "anaconda3-5.2.0",
    "anaconda3-5.3.0",
]
IRONPYTHON = [
    "ironpython-dev",
    "ironpython-2.7.4",
    "ironpython-2.7.5",
    "ironpython-2.7.6.3",
    "ironpython-2.7.7",
]
ACTIVEPYTHON = ["activepython-2.7.14", "activepython-3.5.4", "activepython-3.6.0"]
PYTHON = [
    "2.7.11",
    "2.7.12",
    "2.7.13",
    "2.7.14",
    "2.7.14rc1",
    "2.7.15",
    "3.6.6",
    "3.6.7",
    "3.7.0",
    "3.7-dev",
    "3.7.1",
    "3.8-dev",
]


@pytest.fixture
def pathlib_tmpdir(request, tmpdir):
    yield vistir.compat.Path(str(tmpdir))
    try:
        tmpdir.remove(ignore_errors=True)
    except Exception:
        pass


def _create_tracked_dir():
    temp_args = {"prefix": "pythonfinder-", "suffix": "-test"}
    temp_args["dir"] = os.path.dirname(os.getcwd())
    temp_path = vistir.path.create_tracked_tempdir(**temp_args)
    return temp_path


@pytest.fixture
def vistir_tmpdir():
    temp_path = _create_tracked_dir()
    yield vistir.compat.Path(temp_path)


@pytest.fixture(name="create_tmpdir")
def vistir_tmpdir_factory():
    def create_tmpdir():
        return vistir.compat.Path(_create_tracked_dir())

    yield create_tmpdir


@pytest.fixture
def setup_pythons(create_tmpdir):
    runner = click.testing.CliRunner()
    fake_root_path = create_tmpdir()
    fake_root = fake_root_path.as_posix()
    vistir.path.set_write_bit(fake_root)
    with vistir.contextmanagers.temp_environ(), vistir.contextmanagers.cd(fake_root):
        home_dir = pythonfinder.utils.normalize_path(os.getcwd())
        # This is pip's isolation approach, swipe it for now for time savings
        if sys.platform == "win32":
            home_drive, home_path = os.path.splitdrive(home_dir)
            os.environ.update(
                {"USERPROFILE": home_dir, "HOMEDRIVE": home_drive, "HOMEPATH": home_path}
            )
            for env_var, sub_path in (
                ("APPDATA", "AppData/Roaming"),
                ("LOCALAPPDATA", "AppData/Local"),
            ):
                path = os.path.join(home_dir, *sub_path.split("/"))
                os.environ[env_var] = path
                vistir.path.mkdir_p(path)
        else:
            os.environ["HOME"] = home_dir
            os.environ["XDG_DATA_HOME"] = os.path.join(home_dir, ".local", "share")
            os.environ["XDG_CONFIG_HOME"] = os.path.join(home_dir, ".config")
            os.environ["XDG_CACHE_HOME"] = os.path.join(home_dir, ".cache")
            os.environ["XDG_RUNTIME_DIR"] = os.path.join(home_dir, ".runtime")
            vistir.path.mkdir_p(os.path.join(home_dir, ".cache"))
            vistir.path.mkdir_p(os.path.join(home_dir, ".config"))
            vistir.path.mkdir_p(os.path.join(home_dir, ".local", "share"))
            vistir.path.mkdir_p(os.path.join(fake_root, "usr", "local", "share"))
            vistir.path.mkdir_p(os.path.join(fake_root, "usr", "share"))
            os.environ["XDG_DATA_DIRS"] = ":".join(
                [
                    os.path.join(fake_root, "usr", "local", "share"),
                    os.path.join(fake_root, "usr", "share"),
                ]
            )
        pyenv_dir = os.path.join(home_dir, ".pyenv")
        asdf_dir = os.path.join(home_dir, ".asdf")
        pyenv_shim_dir = os.path.join(pyenv_dir, "shims")
        asdf_shim_dir = os.path.join(asdf_dir, "shims")
        vistir.path.mkdir_p(pyenv_shim_dir)
        vistir.path.mkdir_p(asdf_shim_dir)
        env_path = os.pathsep.join([pyenv_shim_dir, asdf_shim_dir, os.defpath])
        os.environ["PATH"] = env_path
        all_versions = {}
        vistir.path.set_write_bit(fake_root)
        pyenv_python_dir = os.path.join(pyenv_dir, "versions")
        asdf_python_dir = os.path.join(asdf_dir, "installs", "python")
        for python in itertools.chain(
            STACKLESS,
            PYPY,
            PYSTON,
            MINICONDA,
            MICROPYTHON,
            JYTHON,
            ANACONDA,
            IRONPYTHON,
            ACTIVEPYTHON,
            PYTHON,
        ):
            for base_plugin_dir, shim_dir in (
                (pyenv_python_dir, pyenv_shim_dir),
                (asdf_python_dir, asdf_shim_dir),
            ):
                bin_dir = os.path.join(base_plugin_dir, python, "bin")
                vistir.path.mkdir_p(bin_dir)
                vistir.path.set_write_bit(bin_dir)
                vistir.path.set_write_bit(base_plugin_dir)
                python_version = random.choice(["python3.7m", "python3.6m", "python2.7"])
                all_versions[python] = os.path.join(bin_dir, python_version)
                for exe in ["python", python_version, python]:
                    os.link(sys.executable, os.path.join(bin_dir, exe))
                if os.name == "nt":
                    vistir.compat.Path(shim_dir).joinpath(python).touch()
                else:
                    os.symlink(
                        os.path.join(bin_dir, python), os.path.join(shim_dir, python)
                    )
        os.environ["PYENV_ROOT"] = pyenv_dir
        os.environ["ASDF_DIR"] = asdf_dir
        os.environ["ASDF_DATA_DIR"] = asdf_dir
        try:
            yield all_versions
        finally:
            pass


@pytest.fixture
def special_character_python(tmpdir):
    finder = pythonfinder.Finder(
        global_search=True, system=False, ignore_unsupported=True
    )
    python = finder.find_python_version("2")
    python_name = "{0}+".format(python.name)
    python_folder = tmpdir.mkdir(python_name)
    bin_dir = python_folder.mkdir("bin")
    python_path = bin_dir.join("python")
    os.link(python.path.as_posix(), python_path.strpath)
    return python_path


@pytest.fixture(autouse=True)
def setup_env():
    with vistir.contextmanagers.temp_environ():
        os.environ["ANSI_COLORS_DISABLED"] = str("1")


@pytest.fixture()
def expected_python_versions():
    if os.name != "nt":
        return _build_python_tuples()
    return get_windows_python_versions()


def _build_python_tuples():
    finder = pythonfinder.Finder(
        global_search=True, system=False, ignore_unsupported=True
    )
    finder_versions = finder.find_all_python_versions()
    versions = []
    for v in finder_versions:
        if not v.is_python:
            continue
        version = v.as_python
        if not version:
            continue
        arch = (
            version.architecture
            if version.architecture
            else pythonfinder.environment.SYSTEM_ARCH
        )
        arch = arch.replace("bit", "")
        path = vistir.path.normalize_path(v.path)
        version = str(version.version)
        versions.append(pythoninfo(version, path, arch))
    return versions


@pytest.fixture(scope="session")
def all_python_versions():
    return _build_python_tuples()


def get_windows_python_versions():
    c = vistir.misc.run(
        "py -0p",
        block=True,
        nospin=True,
        return_object=True,
        combine_stderr=False,
        write_to_stdout=False,
    )
    versions = []
    for line in c.out.splitlines():
        line = line.strip()
        if line and not "Installed Pythons found" in line:
            version, path = line.split("\t")
            version = version.strip().lstrip("-")
            path = vistir.path.normalize_path(path.strip().strip('"'))
            arch = None
            if "-" in version:
                version, _, arch = version.partition("-")
            versions.append(pythoninfo(version, path, arch))
    return versions
