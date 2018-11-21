# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function

import os
import sys

import pytest

import pythonfinder
import vistir


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


@pytest.fixture
def special_character_python(tmpdir):
    finder = pythonfinder.Finder(global_search=True, system=False, ignore_unsupported=True)
    python = finder.find_python_version('2')
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
