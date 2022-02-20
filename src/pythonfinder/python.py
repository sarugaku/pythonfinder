from __future__ import annotations

import dataclasses as dc
from pathlib import Path

from packaging.version import Version
from packaging.version import parse as parse_version

from pythonfinder.utils import get_binary_hash, subprocess_output


@dc.dataclass
class PythonVersion:
    """The single Python version object found by pythonfinder."""

    executable: Path
    _version: Version | None = dc.field(default=None, hash=False, compare=False)
    _architecture: str | None = dc.field(default=None, compare=False, hash=False)

    def is_valid(self) -> bool:
        """Return True if the python is not broken."""
        return True

    @property
    def real_path(self) -> Path:
        """Resolve the symlink if possible and return the real path."""
        return self.executable.resolve()

    @property
    def name(self) -> str:
        """Return the name of the python."""
        return self.executable.name

    @property
    def version(self) -> Version:
        """Return the version of the python."""
        if self._version is None:
            self._version = self._get_version()
        return self._version

    @property
    def major(self) -> int:
        """Return the major version of the python."""
        return self.version.major

    @property
    def minor(self) -> int:
        """Return the minor version of the python."""
        return self.version.minor

    @property
    def patch(self) -> int:
        """Return the micro version of the python."""
        return self.version.micro

    @property
    def is_prerelease(self) -> bool:
        """Return True if the python is a prerelease."""
        return self.version.is_prerelease

    @property
    def is_devrelease(self) -> bool:
        """Return True if the python is a devrelease."""
        return self.version.is_devrelease

    @property
    def architecture(self) -> str:
        if not self._architecture:
            self._architecture = self._get_architecture()
        return self._architecture

    def binary_hash(self) -> str:
        """Return the binary hash of the python."""
        return get_binary_hash(self.real_path)

    def matches(
        self,
        major: int | None = None,
        minor: int | None = None,
        patch: int | None = None,
        pre: bool | None = None,
        dev: bool | None = None,
        name: str | None = None,
        architecture: str | None = None,
    ) -> bool:
        """
        Return True if the python matches the provided criteria.

        :param major: The major version to match.
        :type major: int
        :param minor: The minor version to match.
        :type minor: int
        :param patch: The micro version to match.
        :type patch: int
        :param pre: Whether the python is a prerelease.
        :type pre: bool
        :param dev: Whether the python is a devrelease.
        :type dev: bool
        :param name: The name of the python.
        :type name: str
        :param architecture: The architecture of the python.
        :type architecture: str
        :return: Whether the python matches the provided criteria.
        :rtype: bool
        """
        if major is not None and self.major != major:
            return False
        if minor is not None and self.minor != minor:
            return False
        if patch is not None and self.patch != patch:
            return False
        if pre is not None and self.is_prerelease != pre:
            return False
        if dev is not None and self.is_devrelease != dev:
            return False
        if name is not None and self.name != name:
            return False
        if architecture is not None and self.architecture != architecture:
            return False
        return True

    def __hash__(self) -> int:
        return hash(self.executable)

    def __repr__(self) -> str:
        attrs = ("executable", "version", "architecture", "major", "minor", "patch")
        return "<PythonVersion {}>".format(
            ", ".join(f"{attr}={getattr(self, attr)!r}" for attr in attrs)
        )

    def __str__(self) -> str:
        return f"{self.name} {self.version} ({self.architecture}) @ {self.executable}"

    def _get_version(self) -> Version:
        """Get the version of the python."""
        script = "import platform; print(platform.python_version())"
        version = self._run_script(script).strip()
        return parse_version(version)

    def _get_architecture(self) -> str:
        script = "import platform; print(platform.architecture()[0])"
        return self._run_script(script).strip()

    def _run_script(self, script: str) -> str:
        """Run a script and return the output."""
        command = [self.executable.as_posix(), "-c", script]
        return subprocess_output(*command)

    def __lt__(self, other: PythonVersion) -> bool:
        """Sort by the version, then by length of the executable path."""
        return (self.version, len(self.executable.as_posix())) < (
            other.version,
            len(other.executable.as_posix()),
        )
