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

Using PythonFinder is easy. Simply import it and ask for a python:

.. code-block:: pycon

    >>> from pythonfinder import Finder
    >>> f = Finder()
    >>> f.find_python_version(3, minor=6)
    PythonInfo(path=PosixPath('/home/user/.pyenv/versions/3.6.5/bin/python'), version_str='3.6.5', major=3, minor=6, patch=5, is_prerelease=False, is_postrelease=False, is_devrelease=False, is_debug=False, version=<Version('3.6.5')>, architecture='64bit', company='PythonCore', name='python', executable='/home/user/.pyenv/versions/3.6.5/bin/python')

    >>> f.find_python_version(2)
    PythonInfo(path=PosixPath('/home/user/.pyenv/versions/2.7.15/bin/python'), version_str='2.7.15', major=2, minor=7, patch=15, is_prerelease=False, is_postrelease=False, is_devrelease=False, is_debug=False, version=<Version('2.7.15')>, architecture='64bit', company='PythonCore', name='python', executable='/home/user/.pyenv/versions/2.7.15/bin/python')

Find a named distribution, such as ``anaconda3-5.3.0``:

.. code-block:: pycon

    >>> f.find_python_version("anaconda3-5.3.0")
    PythonInfo(path=PosixPath('/home/user/.pyenv/versions/anaconda3-5.3.0/bin/python'), version_str='3.7.0', major=3, minor=7, patch=0, is_prerelease=False, is_postrelease=False, is_devrelease=False, is_debug=False, version=<Version('3.7.0')>, architecture='64bit', company='Anaconda', name='anaconda3-5.3.0', executable='/home/user/.pyenv/versions/anaconda3-5.3.0/bin/python')

PythonFinder can even find beta releases:

.. code-block:: pycon

    >>> f.find_python_version(3, minor=7, pre=True)
    PythonInfo(path=PosixPath('/home/user/.pyenv/versions/3.7.0b1/bin/python'), version_str='3.7.0b1', major=3, minor=7, patch=0, is_prerelease=True, is_postrelease=False, is_devrelease=False, is_debug=False, version=<Version('3.7.0b1')>, architecture='64bit', company='PythonCore', name='python', executable='/home/user/.pyenv/versions/3.7.0b1/bin/python')

    >>> f.which('python')
    PosixPath('/home/user/.pyenv/versions/3.6.5/bin/python')


Windows Support
****************

PythonFinder natively supports windows via both the *PATH* environment variable and `PEP-514 <https://www.python.org/dev/peps/pep-0514/>`_ compliant finder which comes by default with python 3. Usage on windows becomes:

.. code-block:: pycon

    >>> from pythonfinder import Finder
    >>> f = Finder()
    >>> f.find_python_version(3, minor=6)
    PythonInfo(path=WindowsPath('C:/Program Files/Python36/python.exe'), version_str='3.6.4', major=3, minor=6, patch=4, is_prerelease=False, is_postrelease=False, is_devrelease=False, is_debug=False, version=<Version('3.6.4')>, architecture='64bit', company='PythonCore', name='python', executable='C:/Program Files/Python36/python.exe')

    >>> f.find_python_version(3, minor=7, pre=True)
    PythonInfo(path=WindowsPath('C:/Program Files/Python37/python.exe'), version_str='3.7.0b5', major=3, minor=7, patch=0, is_prerelease=True, is_postrelease=False, is_devrelease=False, is_debug=False, version=<Version('3.7.0b5')>, architecture='64bit', company='PythonCore', name='python', executable='C:/Program Files/Python37/python.exe')

    >>> f.which('python')
    WindowsPath('C:/Python27/python.exe')

Finding Executables
///////////////////

PythonFinder also provides **which** functionality across platforms, and it uses lazy loading and fast-returns to be performant at this task.

.. code-block:: pycon

    >>> f.which('cmd')
    WindowsPath('C:/windows/system32/cmd.exe')

    >>> f.which('code')
    WindowsPath('C:/Program Files/Microsoft VS Code/bin/code')

     >>> f.which('vim')
    PosixPath('/usr/bin/vim')

    >>> f.which('inv')
    PosixPath('/home/user/.pyenv/versions/3.6.5/bin/inv')


Architecture support
////////////////////

PythonFinder supports architecture specific lookups on all platforms:

.. code-block:: pycon

    >>> f.find_python_version(3, minor=6, arch="64")
    PythonInfo(path=PosixPath('/usr/bin/python3'), version_str='3.6.7', major=3, minor=6, patch=7, is_prerelease=False, is_postrelease=False, is_devrelease=False, is_debug=False, version=<Version('3.6.7')>, architecture='64bit', company='PythonCore', name='python3', executable='/usr/bin/python3')


Integrations
*************

* `Pyenv <https://github.com/pyenv/pyenv>`_
* `ASDF <https://github.com/asdf-vm/asdf>`_
* `PEP-514 <https://www.python.org/dev/peps/pep-0514/>`_
* `Virtualenv <https://github.com/pypa/virtualenv>`_
* `Pipenv <https://pipenv.org>`_


.. click:: pythonfinder.cli:cli
   :prog: pythonfinder
   :show-nested:
