# -*- coding=utf-8 -*-
from __future__ import absolute_import, print_function

import pytest
import pythonfinder
import os
import sys


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


@pytest.fixture(autouse=True)
def setup_env():
    with vistir.contextmanagers.temp_environ():
        os.environ["ANSI_COLORS_DISABLED"] = str("1")
