# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function

import logging

from collections import defaultdict

import attr

from vistir.compat import Path

from ..utils import ensure_path, optional_instance_of
from .mixins import BaseFinder
from .path import VersionPath
from .python import PythonVersion


logger = logging.getLogger(__name__)


@attr.s
class PyenvFinder(BaseFinder):
    root = attr.ib(default=None, validator=optional_instance_of(Path))
    # ignore_unsupported should come before versions, because its value is used
    # in versions's default initializer.
    ignore_unsupported = attr.ib(default=False)
    versions = attr.ib()
    pythons = attr.ib()

    @versions.default
    def get_versions(self):
        versions = defaultdict(VersionPath)
        for p in self.root.glob("versions/*"):
            try:
                version = PythonVersion.parse(p.name)
            except Exception:
                if not self.ignore_unsupported:
                    raise
                logger.warning(
                    'Unsupported Python version %r, ignoring...',
                    p.name, exc_info=True
                )
                continue
            version_tuple = (
                version.get("major"),
                version.get("minor"),
                version.get("patch"),
                version.get("is_prerelease"),
                version.get("is_devrelease"),
            )
            versions[version_tuple] = VersionPath.create(
                path=p.resolve(), only_python=True
            )
        return versions

    @pythons.default
    def get_pythons(self):
        pythons = defaultdict()
        for v in self.versions.values():
            for p in v.paths.values():
                _path = ensure_path(p.path)
                if p.is_python:
                    pythons[_path] = p
        return pythons

    @classmethod
    def create(cls, root, ignore_unsupported=False):
        root = ensure_path(root)
        return cls(root=root, ignore_unsupported=ignore_unsupported)
