# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function

import os
import random
import stat
import sys
from collections import namedtuple

import click
import click.testing
import pytest
import six
import vistir

import pythonfinder

from .testutils import normalized_match, yield_versions

pythoninfo = namedtuple("PythonVersion", ["name", "version", "path", "arch"])


def pytest_runtest_setup(item):
    if item.get_marker("skip_nt") is not None and os.name == "nt":
        pytest.skip("does not run on windows")


@pytest.fixture
def pathlib_tmpdir(request, tmpdir):
    yield vistir.compat.Path(str(tmpdir))
    try:
        tmpdir.remove(ignore_errors=True)
    except Exception:
        pass


def _create_tracked_dir():
    temp_args = {"prefix": "pythonfinder-", "suffix": "-test"}
    temp_args["dir"] = os.environ.get("TMPDIR", "/tmp")
    if temp_args["dir"] == "/":
        temp_args["dir"] = os.getcwd()
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
def no_virtual_env():
    with vistir.contextmanagers.temp_environ():
        if "VIRTUAL_ENV" in os.environ["PATH"]:
            orig_path = os.environ["PATH"].split(os.pathsep)
            venv = vistir.path.normalize_path(os.environ["VIRTUAL_ENV"])
            match = next(iter(p for p in orig_path if normalized_match(p, venv)), None)
            if match:
                orig_path.remove(match)
            del os.environ["VIRTUAL_ENV"]
            os.environ["PATH"] = os.pathsep.join(orig_path)
        yield


@pytest.fixture
def no_pyenv_root_envvar(monkeypatch):
    """This captures a bug hynek ran into where he had no `PYENV_ROOT`.

    When `PYENV_ROOT` is unset we still need to find pythons in the appropriate location
    """

    with monkeypatch.context() as m:
        if "PYENV_ROOT" in os.environ:
            m.delenv("PYENV_ROOT")
        if "ASDF_DATA_DIR" in os.environ:
            m.delenv("ASDF_DATA_DIR")
        six.moves.reload_module(pythonfinder.environment)
        six.moves.reload_module(pythonfinder.models.path)
        m.setattr(pythonfinder.environment, "PYENV_INSTALLED", False)
        m.setattr(pythonfinder.environment, "ASDF_INSTALLED", False)
        m.setattr(
            pythonfinder.environment, "PYENV_ROOT", vistir.path.normalize_path("~/.pyenv")
        )
        m.setattr(
            pythonfinder.environment,
            "ASDF_DATA_DIR",
            vistir.path.normalize_path("~/.asdf"),
        )
        m.setattr(
            pythonfinder.environment,
            "SHIM_PATHS",
            pythonfinder.environment.get_shim_paths(),
        )
        yield


@pytest.fixture
def isolated_envdir(create_tmpdir):
    runner = click.testing.CliRunner()
    fake_root_path = create_tmpdir()
    fake_root = fake_root_path.as_posix()
    vistir.path.set_write_bit(fake_root)
    with vistir.contextmanagers.temp_environ(), vistir.contextmanagers.cd(fake_root):
        home_dir_path = fake_root_path.joinpath("home/pythonfinder")
        home_dir_path.mkdir(parents=True)
        home_dir = vistir.path.normalize_path(home_dir_path.as_posix())
        os.chdir(home_dir)
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
        os.environ["PATH"] = os.defpath
        yield home_dir_path


def setup_plugin(name):
    target = os.path.expandvars(os.path.expanduser("~/.{0}".format(name)))
    this = vistir.compat.Path(__file__).absolute().parent
    plugin_dir = this / "test_artifacts" / name
    plugin_uri = plugin_dir.as_uri()
    if not "file:///" in plugin_uri and "file:/" in plugin_uri:
        plugin_uri = plugin_uri.replace("file:/", "file:///")
    out, err = vistir.misc.run(
        ["git", "clone", plugin_uri, vistir.compat.Path(target).as_posix()], nospin=True
    )
    print(err, file=sys.stderr)
    print(out, file=sys.stderr)


def build_python_versions(path, link_to=None):
    all_versions = {}
    for python_name, python_version in yield_versions():
        python_dir = path / python_name
        bin_dir = python_dir / "bin"
        bin_dir.mkdir(parents=True)
        vistir.path.set_write_bit(bin_dir.as_posix())
        executable_names = [
            python_name,
            "python",
            "python{0}".format(python_version[0]),
            "python{0}".format(python_version[:3]),
        ]
        for executable in executable_names:
            exe_file = bin_dir.joinpath(executable)
            if (
                python_name.startswith("anaconda")
                and not bin_dir.joinpath("anaconda").exists()
            ):
                os.link(sys.executable, str(bin_dir.joinpath("anaconda")))
                os.chmod(bin_dir.joinpath("anaconda").as_posix(), stat.S_IEXEC)
            os.link(sys.executable, str(exe_file))
            os.chmod(exe_file.as_posix(), stat.S_IEXEC)
        all_versions[python_name] = bin_dir / executable_names[3]
        if link_to:
            target = link_to.joinpath(python_name)
            other_target = link_to.joinpath(executable_names[3])
            if os.name == "nt":
                os.link(exe_file.as_posix(), target.as_posix())
                os.link(exe_file.as_posix(), other_target.as_posix())
            else:
                target.symlink_to(exe_file.as_posix())
                if not other_target.exists():
                    other_target.symlink_to(exe_file.as_posix())
                if python_name.startswith("anaconda"):
                    anaconda_target = link_to.joinpath("anaconda")
                    if not anaconda_target.exists():
                        anaconda_target.symlink_to(exe_file.as_posix())
    return all_versions


def setup_pyenv(home_dir):
    pyenv_dir = home_dir / ".pyenv"
    pyenv_shim_dir = pyenv_dir / "shims"
    pyenv_shim_dir.mkdir(parents=True)
    env_path = os.pathsep.join(
        [pyenv_shim_dir.as_posix(), os.environ.get("PATH", os.defpath)]
    )
    os.environ["PATH"] = env_path
    pyenv_python_dir = pyenv_dir / "versions"
    all_versions = build_python_versions(pyenv_python_dir, link_to=pyenv_shim_dir)
    os.environ["PYENV_ROOT"] = pyenv_dir.as_posix()
    return all_versions


def setup_asdf(home_dir):
    asdf_dir = home_dir / ".asdf"
    asdf_shim_dir = asdf_dir / "shims"
    asdf_shim_dir.mkdir(parents=True)
    env_path = os.pathsep.join(
        [asdf_shim_dir.as_posix(), os.environ.get("PATH", os.defpath)]
    )
    os.environ["PATH"] = env_path
    asdf_python_dir = asdf_dir / "installs/python"
    all_versions = build_python_versions(asdf_python_dir, link_to=asdf_shim_dir)
    os.environ["ASDF_DIR"] = asdf_dir.as_posix()
    os.environ["ASDF_DATA_DIR"] = asdf_dir.as_posix()
    return all_versions


@pytest.fixture
def setup_pythons(isolated_envdir, monkeypatch):
    with monkeypatch.context() as m:
        setup_plugin("asdf")
        setup_plugin("pyenv")
        asdf_dict = setup_asdf(isolated_envdir)
        pyenv_dict = setup_pyenv(isolated_envdir)
        os.environ["PATH"] = os.environ.get("PATH").replace("::", ":")
        version_dicts = {"pyenv": pyenv_dict, "asdf": asdf_dict}
        shim_paths = [
            vistir.path.normalize_path(isolated_envdir.joinpath(p).as_posix())
            for p in [".asdf/shims", ".pyenv/shims"]
        ]
        m.setattr("pythonfinder.environment.get_shim_paths", lambda: shim_paths)
        m.setattr("pythonfinder.environment.SHIM_PATHS", shim_paths)
        yield version_dicts


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
        if version.name.startswith("python"):
            name = str(version.version)
        else:
            name = version.name
        path = vistir.path.normalize_path(v.path)
        version = str(version.version)
        versions.append(pythoninfo(name, version, path, arch))
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
            versions.append(pythoninfo(version, version, path, arch))
    return versions
