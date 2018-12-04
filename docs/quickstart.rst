PythonFinder: Cross Platform Search Tool for Finding Pythons
=============================================================

.. image:: https://img.shields.io/pypi/v/pythonfinder.svg
    :target: https://pypi.org/pypi/pythonfinder

.. image:: https://img.shields.io/pypi/l/pythonfinder.svg
    :target: https://pypi.org/pypi/pythonfinder

.. image:: https://img.shields.io/pypi/pyversions/pythonfinder.svg
    :target: https://pypi.org/pypi/pythonfinder

.. image:: https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg
    :target: https://saythanks.io/to/techalchemy

.. image:: https://readthedocs.org/projects/pythonfinder/badge/?version=master
    :target: http://pythonfinder.readthedocs.io/en/master/?badge=master
    :alt: Documentation Status

Installation
*************

Install from `PyPI`_:

.. code-block:: console

    $ pipenv install pythonfinder

Install from `Github`_:

.. code-block:: console

    $ pipenv install -e git+https://github.com/sarugaku/pythonfinder.git#egg=pythonfinder


.. _PyPI: https://www.pypi.org/project/pythonfinder
.. _Github: https://github.com/sarugaku/pythonfinder


.. _`Usage`:

Usage
******

Using PythonFinder is easy.  Simply import it and ask for a python:

.. code-block:: pycon

    >>> from pythonfinder.pythonfinder import PythonFinder
    >>> PythonFinder.from_line('python3')
    '/home/techalchemy/.pyenv/versions/3.6.5/python3'

    >>> from pythonfinder import Finder
    >>> f = Finder()
    >>> f.find_python_version(3, minor=6)
    PathEntry(path=PosixPath('/home/hawk/.pyenv/versions/3.6.5/bin/python'), _children={}, is_root=False, only_python=False, py_version=PythonVersion(major=3, minor=6, patch=5, is_prerelease=False, is_postrelease=False, is_devrelease=False, version=<Version('3.6.5')>, architecture='64bit', comes_from=PathEntry(path=PosixPath('/home/hawk/.pyenv/versions/3.6.5/bin/python'), _children={}, is_root=True, only_python=False, py_version=None, pythons=None), executable=None), pythons=None)
    >>> f.find_python_version(2)
    PathEntry(path=PosixPath('/home/hawk/.pyenv/shims/python2'), ...py_version=PythonVersion(major=2, minor=7, patch=15, is_prerelease=False, is_postrelease=False, is_devrelease=False, version=<Version('2.7.15')>, architecture='64bit', comes_from=PathEntry(path=PosixPath('/home/hawk/.pyenv/shims/python2'), _children={}, is_root=True, only_python=False, py_version=None, pythons=None), executable=None), pythons=None)
    >>> f.find_python_version("anaconda3-5.3.0")

Find a named distribution, such as ``anaconda3-5.3.0``:

.. code-block:: pycon

    PathEntry(path=PosixPath('/home/hawk/.pyenv/versions/anaconda3-5.3.0/bin/python3.7m'), _children={'/home/hawk/.pyenv/versions/anaconda3-5.3.0/bin/python3.7m': ...}, only_python=False, name='anaconda3-5.3.0', _py_version=PythonVersion(major=3, minor=7, patch=0, is_prerelease=False, is_postrelease=False, is_devrelease=False,...))

PythonFinder can even find beta releases:

.. code-block:: pycon

    >>> f.find_python_version(3, minor=7)
    PathEntry(path=PosixPath('/home/hawk/.pyenv/versions/3.7.0b1/bin/python'), _children={}, is_root=False, only_python=False, py_version=PythonVersion(major=3, minor=7, patch=0, is_prerelease=True, is_postrelease=False, is_devrelease=False, version=<Version('3.7.0b1')>, architecture='64bit', comes_from=PathEntry(path=PosixPath('/home/hawk/.pyenv/versions/3.7.0b1/bin/python'), _children={}, is_root=True, only_python=False, py_version=None, pythons=None), executable=None), pythons=None)

    >>> f.which('python')
    PathEntry(path=PosixPath('/home/hawk/.pyenv/versions/3.6.5/bin/python'), _children={}, is_root=False, only_python=False, py_version=PythonVersion(major=3, minor=6, patch=5, is_prerelease=False, is_postrelease=False, is_devrelease=False, version=<Version('3.6.5')>, architecture='64bit', comes_from=PathEntry(path=PosixPath('/home/hawk/.pyenv/versions/3.6.5/bin/python'), _children={}, is_root=True, only_python=False, py_version=None, pythons=None), executable=None), pythons=None)


Windows Support
****************

PythonFinder natively supports windows via both the *PATH* environment variable and `PEP-514 <https://www.python.org/dev/peps/pep-0514/>`_ compliant finder which comes by default with python 3. Usage on windows becomes:

.. code-block:: pycon

    >>> from pythonfinder import Finder
    >>> f = Finder()
    >>> f.find_python_version(3, minor=6)
    PythonVersion(major=3, minor=6, patch=4, is_prerelease=False, is_postrelease=False, is_devrelease=False, version=<Version('3.6.4')>, architecture='64bit', comes_from=PathEntry(path=WindowsPath('C:/Program Files/Python36/python.exe'), _children={}, is_root=False, only_python=True, py_version=None, pythons=None), executable=WindowsPath('C:/Program Files/Python36/python.exe'))

    >>> f.find_python_version(3, minor=7, pre=True)
    PythonVersion(major=3, minor=7, patch=0, is_prerelease=True, is_postrelease=False, is_devrelease=False, version=<Version('3.7.0b5')>, architecture='64bit', comes_from=PathEntry(path=WindowsPath('C:/Program Files/Python37/python.exe'), _children={}, is_root=False, only_python=True, py_version=None, pythons=None), executable=WindowsPath('C:/Program Files/Python37/python.exe'))

    >>> f.which('python')
    PathEntry(path=WindowsPath('C:/Python27/python.exe'), _children={}, is_root=False, only_python=False, py_version=None, pythons=None)

Finding Executables
///////////////////

PythonFinder also provides **which** functionality across platforms, and it uses lazy loading and fast-returns to be performant at this task.

.. code-block:: pycon

    >>> f.which('cmd')
    PathEntry(path=WindowsPath('C:/windows/system32/cmd.exe'), _children={}, is_root=False, only_python=False, py_version=None, pythons=None)

    >>> f.which('code')
    PathEntry(path=WindowsPath('C:/Program Files/Microsoft VS Code/bin/code'), _children={}, is_root=False, only_python=False, py_version=None, pythons=None)

     >>> f.which('vim')
    PathEntry(path=PosixPath('/usr/bin/vim'), _children={}, is_root=False, only_python=False, py_version=None, pythons=None)

    >>> f.which('inv')
    PathEntry(path=PosixPath('/home/hawk/.pyenv/versions/3.6.5/bin/inv'), _children={}, is_root=False, only_python=False, py_version=None, pythons=None)


Architecture support
////////////////////

PythonFinder supports architecture specific lookups on all platforms:

.. code-block:: pycon

    >>> f.find_python_version(3, minor=6, arch="64")
    PathEntry(path=PosixPath('/usr/bin/python3'), _children={'/usr/bin/python3': ...}, only_python=False, name='python3', _py_version=PythonVersion(major=3, minor=6, patch=7, is_prerelease=False, is_postrelease=False, is_devrelease=False, is_debug=False, version=<Version('3.6.7')>, architecture='64bit', comes_from=..., executable='/usr/bin/python3', name='python3'), _pythons=defaultdict(None, {}), is_root=False)


Integrations
*************

* `Pyenv <https://github.com/pyenv/pyenv>`_
* `ASDF <https://github.com/asdf-vm/asdf>`_
* `PEP-514 <https://www.python.org/dev/peps/pep-0514/>`_
* `Virtualenv <https://github.com/pypa/virtualenv>`_
* `Pipenv <https://pipenv.org>`_


.. click:: pythonfinder:cli
   :prog: pyfinder
   :show-nested:
