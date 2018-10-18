1.1.3 (2018-10-18)
==================

Features & Improvements
-----------------------

- Introduced lookup by name when searching for python versions, which allows searching for non-standard python releases such as ``anaconda3-5.3.0``.  `#20 <https://github.com/sarugaku/pythonfinder/issues/20>`_
  
- General improvements:
    - Improved ``pyenv`` support and architecture lookup support.
    - Improved overall performance and caching.  `#21 <https://github.com/sarugaku/pythonfinder/issues/21>`_
  

Bug Fixes
---------

- Switch to using ``--ignore-unsupported`` by default during lookups.  `#19 <https://github.com/sarugaku/pythonfinder/issues/19>`_


1.1.2 (2018-10-12)
==================

Features & Improvements
-----------------------

- Added support for non-CPython interpreters.  `#16 <https://github.com/sarugaku/pythonfinder/issues/16>`_
  

Bug Fixes
---------

- Added support for ignoring unsupported python versions during version search with the flag ``--ignore-unsupported``.  `#14 <https://github.com/sarugaku/pythonfinder/issues/14>`_
  
- Added support for pyenv virtualenvs.  `#15 <https://github.com/sarugaku/pythonfinder/issues/15>`_


1.1.1 (2018-10-11)
==================

Bug Fixes
---------

- Fixed an issue which prevented graceful parsing of debug releases of python, which will now be sorted the same as prereleases.  `#12 <https://github.com/sarugaku/pythonfinder/issues/12>`_


1.1.0 (2018-10-06)
==================

Bug Fixes
---------

- Fixed a bug which caused inadvertent inclusion of previously removed python installations on windows.  `#11 <https://github.com/sarugaku/pythonfinder/issues/11>`_


1.0.2 (2018-08-15)
==================

Bug Fixes
---------

- Fix a bug which caused failures when parsing patch releases.  `#10 <https://github.com/sarugaku/pythonfinder/issues/10>`_


1.0.1 (2018-07-31)
==================

Bug Fixes
---------

- Fix input string parser when architecture is specified.  `#9 <https://github.com/sarugaku/pythonfinder/issues/9>`_


1.0.0 (2018-07-25)
==================

Features & Improvements
-----------------------

- Add support for explicitly searching the global pythonpath using the ``global_search`` argument at initialization.  `#4 <https://github.com/sarugaku/pythonfinder/issues/4>`_
  
- Allow bare calls to ``find_all_python_versions()`` to return all python versions without specifying a major version.  `#5 <https://github.com/sarugaku/pythonfinder/issues/5>`_
  
- Added efficient crawling and caching when searching for python and other executables.

  - Carry architecture support all the way through the search stack to only return available python which matches the desired architecture.
  - Improve sub-path consolidations for searching for executables and pythons.
  - Use lazy loading of python versions to avoid unnecessary subprocess calls.  `#8 <https://github.com/sarugaku/pythonfinder/issues/8>`_
  

Bug Fixes
---------

- Fixed a bug which caused version checks on older python versions to fail due to encoding issues.  `#3 <https://github.com/sarugaku/pythonfinder/issues/3>`_
  
- Prevent use of ``VIRTUAL_ENV`` as a search location when ``global_search`` is ``False``.  `#4 <https://github.com/sarugaku/pythonfinder/issues/4>`_
  
- Fixed an issue which sometimes caused pythonfinder to prefer prerelease versions.  `#7 <https://github.com/sarugaku/pythonfinder/issues/7>`_
