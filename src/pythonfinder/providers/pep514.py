from __future__ import annotations

import platform
from pathlib import Path
from typing import Iterable, Type

from packaging.version import parse as parse_version

from pythonfinder.providers.base import BaseProvider, T
from pythonfinder.python import PythonVersion
from pythonfinder.utils import WINDOWS

SYS_ARCHITECTURE = platform.architecture()[0]


class Pep514Provider(BaseProvider):
    """A provider that finds Python from the winreg."""

    @classmethod
    def create(cls: Type[T]) -> T | None:
        if not WINDOWS:
            return None
        return cls()

    def find_pythons(self) -> Iterable[PythonVersion]:
        from pythonfinder._vendor.pep514tools import findall as pep514_findall

        env_versions = pep514_findall()
        for version in env_versions:
            install_path = getattr(version.info, "install_path", None)
            if install_path is None:
                continue
            try:
                path = Path(install_path.value)
            except AttributeError:
                continue
            if path.exists():
                py_ver = PythonVersion(
                    path,
                    parse_version(version.info.version),
                    getattr(version.info, "sys_architecture", SYS_ARCHITECTURE),
                )
                if py_ver.is_valid():
                    yield py_ver
