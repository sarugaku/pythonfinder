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
