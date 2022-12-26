#!env python


import os
import sys

from pythonfinder.cli import cli

PYTHONFINDER_MAIN = os.path.dirname(os.path.abspath(__file__))
PYTHONFINDER_PACKAGE = os.path.dirname(PYTHONFINDER_MAIN)


if __name__ == "__main__":
    sys.exit(cli())
