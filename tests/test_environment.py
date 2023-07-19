from __future__ import annotations

import os
import re
import tempfile

import pytest

from pythonfinder.environment import possibly_convert_to_windows_style_path


@pytest.mark.skipif(os.name != 'nt', reason="Only run on Windows")
def test_possibly_convert_to_windows_style_path():
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Get an input path in the form "\path\to\tempdir"
        drive, tail = os.path.splitdrive(tmpdirname)
        input_path = tail.replace('/', '\\')
        assert re.match(r"(\\[^/\\]+)+", input_path)
        revised_path = possibly_convert_to_windows_style_path(input_path)
        assert input_path == revised_path

        # Get an input path in the form "/c/path/to/tempdir"
        input_path = '/' + drive[0].lower() + tail.replace('\\', '/')
        assert re.match(r"/[a-z](/[^/\\]+)+", input_path)
        expected = drive.upper() + tail.replace('/', '\\')
        revised_path = possibly_convert_to_windows_style_path(input_path)
        assert expected == revised_path
