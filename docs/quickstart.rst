PythonFinder: Cross Platform Search Tool for Finding Pythons
=============================================================

.. image:: https://img.shields.io/pypi/v/pythonfinder.svg
    :target: https://pypi.python.org/pypi/pythonfinder

.. image:: https://img.shields.io/pypi/l/pythonfinder.svg
    :target: https://pypi.python.org/pypi/pythonfinder

.. image:: https://img.shields.io/pypi/pyversions/pythonfinder.svg
    :target: https://pypi.python.org/pypi/pythonfinder

.. image:: https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg
    :target: https://saythanks.io/to/techalchemy

.. image:: https://readthedocs.org/projects/pythonfinder/badge/?version=latest
    :target: http://pythonfinder.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


Installation
*************

Install from `PyPI`_:

  ::

    $ pipenv install --pre pythonfinder

Install from `Github`_:

  ::

    $ pipenv install -e git+https://github.com/techalchemy/pythonfinder.git#egg=pythonfinder


.. _PyPI: https://www.pypi.org/project/pythonfinder
.. _Github: https://github.com/techalchemy/pythonfinder


.. _`Usage`:

Usage
******

Using PythonFinder is easy.  Simply import it and ask for a python:

  ::

    >>> from pythonfinder.pythonfinder import PythonFinder
    >>> PythonFinder.from_line('python3')
    '/home/techalchemy/.pyenv/versions/3.6.5/python3'

    >>> PythonFinder.from_version('2.7')
    '/home/techalchemy/.pyenv/versions/2.7.14/python'

PythonFinder can even find beta releases!

  ::

    >>> PythonFinder.from_version('3.7')
    '/home/techalchemy/.pyenv/versions/3.7.0b1/bin/python'

Windows Support
****************

PythonFinder natively supports windows via both the *PATH* environment variable and `PEP-514 <https://www.python.org/dev/peps/pep-0514/>`_ compliant finder which comes by default with python 3. Usage on windows becomes:

  ::

    >>> PythonFinder.from_line('python')
    WindowsPath('C:/Program Files/Python36/python.exe')

    >>> PythonFinder.from_version('2.7')
    WindowsPath('C:/Python27/python.exe')

    >>> PythonFinder.from_version('3.6')
    WindowsPath('C:/Program Files/Python36/python.exe')

    >>> PythonFinder.from_line('py -3')
    WindowsPath('C:/Program Files/Python36/python.exe')

Architecture support
////////////////////

PythonFinder supports architecture specific lookups on Windows:

  ::

    >>> PythonFinder.from_version('2.7', architecture='64bit')
    WindowsPath('C:/Python27/python.exe')


Integrations
*************

* `Pyenv <https://github.com/pyenv/pyenv>`_
* `PEP-514 <https://www.python.org/dev/peps/pep-0514/>`_
* `Virtualenv <https://github.com/pypa/virtualenv>`_
* `Pipenv <https://pipenv.org>`_
