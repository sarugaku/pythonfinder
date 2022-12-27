# Add NullHandler to "pythonfinder" logger, because Python2's default root
# logger has no handler and warnings like this would be reported:
#
# > No handlers could be found for logger "pythonfinder.models.pyenv"
from __future__ import annotations

import logging

from .exceptions import InvalidPythonVersion
from .models import SystemPath, WindowsFinder
from .pythonfinder import Finder

__version__ = "1.3.3.dev0"


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = ["Finder", "WindowsFinder", "SystemPath", "InvalidPythonVersion"]
