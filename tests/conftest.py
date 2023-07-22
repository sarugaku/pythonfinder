from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

import pytest

import pythonfinder

from .testutils import (
    cd,
    create_tracked_tempdir,
    normalize_path,
    normalized_match,
    set_write_bit,
    temp_environ,
    yield_versions,
)

pythoninfo = namedtuple("PythonVersion", ["name", "version", "path", "arch"])


@pytest.fixture
def pathlib_tmpdir(request, tmpdir):
    yield Path(str(tmpdir))
    try:
        tmpdir.remove(ignore_errors=True)
    except Exception:
        pass


def _create_tracked_dir():
    temp_args = {"prefix": "pythonfinder-", "suffix": "-test"}
    temp_args["dir"] = os.environ.get("TMPDIR", "/tmp")
    if temp_args["dir"] == "/":
        temp_args["dir"] = os.getcwd()
    temp_path = create_tracked_tempdir(**temp_args)
    return temp_path


@pytest.fixture
def tracked_tmpdir():
    temp_path = _create_tracked_dir()
    yield Path(temp_path)


@pytest.fixture(name="create_tmpdir")
def tracked_tmpdir_factory():
    def create_tmpdir():
        return Path(_create_tracked_dir())

    yield create_tmpdir


@pytest.fixture
def no_virtual_env():
    with temp_environ():
        if "VIRTUAL_ENV" in os.environ["PATH"]:
            orig_path = os.environ["PATH"].split(os.pathsep)
            venv = normalize_path(os.environ["VIRTUAL_ENV"])
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
        m.setattr(pythonfinder.environment, "PYENV_INSTALLED", False)
        m.setattr(pythonfinder.environment, "ASDF_INSTALLED", False)
        m.setattr(pythonfinder.environment, "PYENV_ROOT", normalize_path("~/.pyenv"))
        m.setattr(
            pythonfinder.environment,
            "ASDF_DATA_DIR",
            normalize_path("~/.asdf"),
        )
        yield


@pytest.fixture
def isolated_envdir(create_tmpdir):
    fake_root_path = create_tmpdir()
    fake_root = fake_root_path.as_posix()
    set_write_bit(fake_root)
    with temp_environ(), cd(fake_root):
        home_dir_path = fake_root_path.joinpath("home/pythonfinder")
        home_dir_path.mkdir(parents=True)
        home_dir = normalize_path(home_dir_path.as_posix())
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
                Path(path).mkdir(exist_ok=True, parents=True)
        else:
            os.environ["HOME"] = home_dir
            os.environ["XDG_DATA_HOME"] = os.path.join(home_dir, ".local", "share")
            os.environ["XDG_CONFIG_HOME"] = os.path.join(home_dir, ".config")
            os.environ["XDG_CACHE_HOME"] = os.path.join(home_dir, ".cache")
            os.environ["XDG_RUNTIME_DIR"] = os.path.join(home_dir, ".runtime")
            Path(os.path.join(home_dir, ".cache")).mkdir(exist_ok=True, parents=True)
            Path(os.path.join(home_dir, ".config")).mkdir(exist_ok=True, parents=True)
            Path(os.path.join(home_dir, ".local", "share")).mkdir(
                exist_ok=True, parents=True
            )
            Path(os.path.join(fake_root, "usr", "local", "share")).mkdir(
                exist_ok=True, parents=True
            )
            Path(os.path.join(fake_root, "usr", "share")).mkdir(
                exist_ok=True, parents=True
            )
            os.environ["XDG_DATA_DIRS"] = ":".join(
                [
                    os.path.join(fake_root, "usr", "local", "share"),
                    os.path.join(fake_root, "usr", "share"),
                ]
            )
        os.environ["PATH"] = os.defpath
        yield home_dir_path


def setup_plugin(name):
    target = os.path.expandvars(os.path.expanduser(f"~/.{name}"))
    this = Path(__file__).absolute().parent
    plugin_dir = this / "test_artifacts" / name
    plugin_uri = plugin_dir.as_uri()
    if "file:///" not in plugin_uri and "file:/" in plugin_uri:
        plugin_uri = plugin_uri.replace("file:/", "file:///")
    out = subprocess.check_output(["git", "clone", plugin_uri, Path(target).as_posix()])
    print(out, file=sys.stderr)


def build_python_versions(path, link_to=None):
    all_versions = {}
    for python_name, python_version in yield_versions():
        python_dir = path / python_name
        bin_dir = python_dir / "bin"
        bin_dir.mkdir(parents=True)
        set_write_bit(bin_dir.as_posix())
        executable_names = [
            "python",
            f"python{python_version[0]}",
            f"python{python_version[:3]}",
        ]
        for executable in executable_names:
            exe_file = bin_dir.joinpath(executable)
            shutil.copy2(sys.executable, str(exe_file))
        all_versions[python_name] = bin_dir / executable_names[-1]
        if link_to:
            target = link_to.joinpath(python_name)
            other_target = link_to.joinpath(executable_names[-1])
            if os.name == "nt":
                os.link(exe_file.as_posix(), target.as_posix())
                os.link(exe_file.as_posix(), other_target.as_posix())
            else:
                target.symlink_to(exe_file.as_posix())
                bin_target = bin_dir.joinpath(python_name)
                if not bin_target.exists():
                    bin_target.symlink_to(exe_file.as_posix())
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
    with monkeypatch.context():
        setup_plugin("asdf")
        setup_plugin("pyenv")
        asdf_dict = setup_asdf(isolated_envdir)
        pyenv_dict = setup_pyenv(isolated_envdir)
        os.environ["PATH"] = os.environ.get("PATH").replace("::", ":")
        version_dicts = {"pyenv": pyenv_dict, "asdf": asdf_dict}
        yield version_dicts


@pytest.fixture
def special_character_python(tmp_path):
    finder = pythonfinder.Finder(
        global_search=False, system=True, ignore_unsupported=True, sort_by_path=True
    )
    python = finder.find_python_version()
    python_name = "2+"
    python_folder = tmp_path / python_name / "bin"
    python_folder.mkdir(parents=True)
    set_write_bit(str(python_folder))
    python_path = python_folder / "python"
    python_path.symlink_to(python.path)
    return python_path


@pytest.fixture(autouse=True)
def setup_env():
    with temp_environ():
        os.environ["ANSI_COLORS_DISABLED"] = "1"


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
        path = normalize_path(v.path)
        version = str(version.version)
        versions.append(pythoninfo(name, version, path, arch))
    return versions


@pytest.fixture(scope="session")
def all_python_versions():
    return _build_python_tuples()


def get_windows_python_versions():
    out = subprocess.check_output("py -0p", shell=True)
    versions = []
    for line in out.splitlines():
        line = line.strip()
        if line and "Installed Pythons found" not in line:
            version, path = line.split("\t")
            version = version.strip().lstrip("-")
            path = normalize_path(path.strip().strip('"'))
            arch = None
            if "-" in version:
                version, _, arch = version.partition("-")
            versions.append(pythoninfo(version, version, path, arch))
    return versions
