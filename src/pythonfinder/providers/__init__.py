"""
This package contains all the providers for the pythonfinder module.
"""
from typing import List, Type

from pythonfinder.providers.asdf import AsdfProvider
from pythonfinder.providers.base import BaseProvider
from pythonfinder.providers.macos import MacOSProvider
from pythonfinder.providers.path import PathProvider
from pythonfinder.providers.pep514 import Pep514Provider
from pythonfinder.providers.pyenv import PyenvProvider

ALL_PROVIDERS: List[Type[BaseProvider]] = [
    # General:
    PathProvider,
    # Tool Specific:
    AsdfProvider,
    PyenvProvider,
    # Windows only:
    Pep514Provider,
    # MacOS only:
    MacOSProvider,
]

__all__ = [cls.__name__ for cls in ALL_PROVIDERS] + ["ALL_PROVIDERS", "BaseProvider"]
