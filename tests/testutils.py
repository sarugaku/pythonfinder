# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import itertools
import os

import vistir


def normalized_match(path, parent):
    return vistir.path.is_in_path(
        vistir.path.normalize_path(path), vistir.path.normalize_path(parent)
    )


def is_in_ospath(path):
    ospath = os.environ["PATH"].split(os.pathsep)
    return any(normalized_match(path, entry) for entry in ospath)


def print_python_versions(versions):
    versions = list(versions)
    if versions:
        vistir.misc.echo("Found python at the following locations:", fg="green", err=True)
        for v in versions:
            py = v.py_version
            comes_from = getattr(py, "comes_from", None)
            if comes_from is not None:
                comes_from_path = getattr(comes_from, "path", v.path)
            else:
                comes_from_path = v.path
            vistir.misc.echo(
                "{py.name!s}: {py.version!s} ({py.architecture!s}) @ {comes_from!s}".format(
                    py=py, comes_from=comes_from_path
                ),
                fg="yellow",
                err=True,
            )


STACKLESS = [
    ("stackless-2.7-dev", "2.7.0"),
    ("stackless-2.7.2", "2.7.2"),
    ("stackless-2.7.3", "2.7.3"),
    ("stackless-2.7.4", "2.7.4"),
    ("stackless-2.7.5", "2.7.5"),
    ("stackless-2.7.6", "2.7.6"),
    ("stackless-2.7.7", "2.7.7"),
    ("stackless-2.7.8", "2.7.8"),
    ("stackless-2.7.9", "2.7.9"),
    ("stackless-2.7.10", "2.7.10"),
    ("stackless-2.7.11", "2.7.11"),
    ("stackless-2.7.12", "2.7.12"),
    ("stackless-2.7.14", "2.7.14"),
    ("stackless-3.2.2", "3.2.2"),
    ("stackless-3.2.5", "3.2.5"),
    ("stackless-3.3.5", "3.3.5"),
    ("stackless-3.3.7", "3.3.7"),
    ("stackless-3.4-dev", "3.4.0"),
    ("stackless-3.4.1", "3.4.1"),
    ("stackless-3.4.2", "3.4.2"),
    ("stackless-3.4.7", "3.4.7"),
    ("stackless-3.5.4", "3.5.4"),
]
PYPY = [
    ("pypy3-2.3.1", "3.3"),
    ("pypy3-2.4.0-src", "3.4"),
    ("pypy3-2.4.0", "3.4"),
    ("pypy2-5.6.0", "2.7"),
    ("pypy2.7-5.10.0", "2.7"),
    ("pypy2.7-6.0.0", "2.7"),
    ("pypy-5.3.1", "2.7.12"),
    ("pypy3.5-5.10.1", "3.5"),
    ("pypy3.5-6.0.0-src", "3.5"),
    ("pypy3.5-6.0.0", "3.5"),
]
# These are definitely no longer supported but people may still have them installed
PYSTON = [("pyston-0.5.1", "2.7.8"), ("pyston-0.6.0", "2.7.8"), ("pyston-0.6.1", "2.7.8")]
MINICONDA = [
    ("miniconda-2.2.2", "2.7"),
    ("miniconda-3.0.0", "2.7"),
    ("miniconda-3.0.4", "2.7"),
    ("miniconda-3.0.5", "2.7"),
    ("miniconda-3.3.0", "2.7"),
    ("miniconda-3.4.2", "2.7"),
    ("miniconda3-3.18.3", "3.5.4"),
    ("miniconda3-3.19.0", "3.5.5"),
    ("miniconda3-4.0.5", "3.6.2"),
    ("miniconda3-4.1.11", "3.6.2"),
    ("miniconda3-4.3.27", "3.7.1"),
    ("miniconda3-4.3.30", "3.7.2"),
]
# I have no idea how these are represented
MICROPYTHON = [("micropython-1.9.3", "1.9.3"), ("micropython-1.9.4", "1.9.4")]
JYTHON = [
    ("jython-2.5-dev", "2.5-dev"),
    ("jython-2.5.1", "2.5.1"),
    ("jython-2.5.2", "2.5.2"),
    ("jython-2.5.3", "2.5.3"),
    ("jython-2.5.4-rc1", "2.5.4-rc1"),
    ("jython-2.7.0", "2.7.0"),
    ("jython-2.7.1", "2.7.1"),
]
ANACONDA = [
    ("anaconda2-2.4.1", "2.7.8"),
    ("anaconda2-2.5.0", "2.7.10"),
    ("anaconda2-4.0.0", "2.7.12"),
    ("anaconda2-4.1.0", "2.7.13"),
    ("anaconda2-4.1.1", "2.7.13"),
    ("anaconda2-4.2.0", "2.7.14"),
    ("anaconda2-4.3.0", "2.7.14"),
    ("anaconda2-4.3.1", "2.7.15"),
    ("anaconda2-4.4.0", "2.7.15"),
    ("anaconda3-4.1.1", "3.4.5"),
    ("anaconda3-4.2.0", "3.5.2"),
    ("anaconda3-4.3.0", "3.5.3"),
    ("anaconda3-4.3.1", "3.5.4"),
    ("anaconda3-4.4.0", "3.5.5"),
    ("anaconda3-5.0.0", "3.6.2"),
    ("anaconda3-5.0.1", "3.6.2"),
    ("anaconda3-5.1.0", "3.6.3"),
    ("anaconda3-5.2.0", "3.6.4"),
    ("anaconda3-5.3.0", "3.6.5"),
    ("anaconda3-2019.03", "3.7.2"),
]
IRONPYTHON = [
    ("ironpython-dev", "2.7.8"),
    ("ironpython-2.7.4", "2.7.4"),
    ("ironpython-2.7.5", "2.7.5"),
    ("ironpython-2.7.6.3", "2.7.6"),
    ("ironpython-2.7.7", "2.7.7"),
]
ACTIVEPYTHON = [
    ("activepython-2.7.14", "2.7.14"),
    ("activepython-3.5.4", "3.5.4"),
    ("activepython-3.6.0", "3.6.0"),
]
PYTHON = [
    ("2.7.11", "2.7.11"),
    ("2.7.12", "2.7.12"),
    ("2.7.13", "2.7.13"),
    ("2.7.14", "2.7.14"),
    ("2.7.14rc1", "2.7.14rc1"),
    ("2.7.15", "2.7.15"),
    ("3.6.6", "3.6.6"),
    ("3.6.7", "3.6.7"),
    ("3.6.8", "3.6.8"),
    ("3.7.0", "3.7.0"),
    ("3.7-dev", "3.7-dev"),
    ("3.7.1", "3.7.1"),
    ("3.7.2", "3.7.2"),
    ("3.7.3", "3.7.3"),
    ("3.8-dev", "3.8-dev"),
]


def yield_versions():
    return itertools.chain(
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
    )
