from __future__ import annotations

import logging
import operator
from typing import Iterable

from pythonfinder.providers import ALL_PROVIDERS, BaseProvider
from pythonfinder.python import PythonVersion
from pythonfinder.utils import parse_major

logger = logging.getLogger("pythonfinder")


class Finder:
    """Find python versions on the system."""

    def __init__(
        self, resolve_symlinks: bool = False, no_same_file: bool = False
    ) -> None:
        self.resolve_symlinks = resolve_symlinks
        self.no_same_file = no_same_file

        self._providers = self.setup_providers()

    def setup_providers(self) -> list[BaseProvider]:
        providers: list[BaseProvider] = []
        for provider_class in ALL_PROVIDERS:
            provider = provider_class.create()
            if provider is None:
                logger.debug("Provider %s is not available", provider_class.__name__)
            else:
                providers.append(provider)
        return providers

    def find_all_python_versions(
        self,
        major: int | str | None = None,
        minor: int | None = None,
        patch: int | None = None,
        pre: bool | None = None,
        dev: bool | None = None,
        name: str | None = None,
        architecture: str | None = None,
    ) -> list[PythonVersion]:
        """
        Return all Python versions matching the given version criteria.

        :param major: The major version or the version string or the name to match.
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
        :return: a list of PythonVersion objects
        :rtype: list
        """
        if isinstance(major, str):
            if any(v is not None for v in (minor, patch, pre, dev, name)):
                raise ValueError(
                    "If major is a string, minor, patch, pre, dev and name "
                    "must not be specified."
                )
            version_dict = parse_major(major)
            if version_dict is not None:
                major = version_dict["major"]
                minor = version_dict["minor"]
                patch = version_dict["patch"]
                pre = version_dict["pre"]
                dev = version_dict["dev"]
            else:
                name, major = major, None

        version_matcher = operator.methodcaller(
            "matches",
            major,
            minor,
            patch,
            pre,
            dev,
            name,
            architecture,
        )
        # Deduplicate with the python executable path
        matched_python = sorted(
            filter(version_matcher, set(self._find_all_python_versions()))
        )
        return self._dedup(matched_python)

    def find_python_version(
        self,
        major: int | str | None = None,
        minor: int | None = None,
        patch: int | None = None,
        pre: bool | None = None,
        dev: bool | None = None,
        name: str | None = None,
        architecture: str | None = None,
    ) -> PythonVersion | None:
        """
        Return the Python version that is closest to the given version criteria.

        :param major: The major version or the version string or the name to match.
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
        :return: a Python object or None
        :rtype: PythonVersion|None
        """
        return next(
            iter(
                self.find_all_python_versions(
                    major, minor, patch, pre, dev, name, architecture
                )
            ),
            None,
        )

    def _find_all_python_versions(self) -> Iterable[PythonVersion]:
        """Find all python versions on the system."""
        for provider in self._providers:
            yield from provider.find_pythons()

    def _dedup(self, python_versions: list[PythonVersion]) -> list[PythonVersion]:
        def dedup_key(python_version: PythonVersion) -> str:
            if self.no_same_file:
                return python_version.binary_hash()
            if self.resolve_symlinks:
                return python_version.real_path.as_posix()
            return python_version.executable.as_posix()

        if not self.resolve_symlinks and not self.no_same_file:
            python_versions.reverse()
        else:
            python_versions = list(
                reversed(
                    {
                        dedup_key(python_version): python_version
                        for python_version in python_versions
                    }.values()
                )
            )
        return python_versions
