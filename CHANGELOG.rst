1.2.1 (2019-05-13)
==================

Features & Improvements
-----------------------

- Added support for subprocess timeouts while discovering python paths.  `#62 <https://github.com/sarugaku/pythonfinder/issues/62>`_


1.2.0 (2019-03-02)
==================

Features & Improvements
-----------------------

- Dramatically improved performance and stability.  `#51 <https://github.com/sarugaku/pythonfinder/issues/51>`_
    
- Added typehints and refactored mixins, updated shims to only attempt to remove themselves if they detect their respectve installations (fixes Hynek's issue).  `#52 <https://github.com/sarugaku/pythonfinder/issues/52>`_
    

Bug Fixes
---------

- Add resilient parsing to look only for ``major.minor(.patch)?`` as a fallback parser and allow more graceful continuation if a path is not a real path to python.  `#40 <https://github.com/sarugaku/pythonfinder/issues/40>`_
    
- Added typehints and refactored mixins, updated shims to only attempt to remove themselves if they detect their respectve installations (fixes Hynek's issue).  `#52 <https://github.com/sarugaku/pythonfinder/issues/52>`_
    
- Fixed a bug which prevented parsing of numeric versions as inputs to pythonfinder.  `#59 <https://github.com/sarugaku/pythonfinder/issues/59>`_
    
- Windows path discovery now works correctly and does not attempt to assign cached properties.  `#61 <https://github.com/sarugaku/pythonfinder/issues/61>`_


1.1.10 (2018-11-22)
===================

Bug Fixes
---------

- Fix a bug where version in version order file may not in global version paths  `#37 <https://github.com/sarugaku/pythonfinder/issues/37>`_
    
- Added further resilient version parser functionality to python version parser.  `#44 <https://github.com/sarugaku/pythonfinder/issues/44>`_
    
- Fixed an issue which prevented parsing single digit python versions as valid.  `#47 <https://github.com/sarugaku/pythonfinder/issues/47>`_


1.1.9 (2018-11-13)
==================

Features & Improvements
-----------------------

- Added performance enhancements and error handling to python search algorithms.    
- Added support for ``asdf`` installations via the ``ASDF_DATA_DIR`` environment variable.  `#35 <https://github.com/sarugaku/pythonfinder/issues/35>`_


1.1.8 (2018-11-12)
==================

Bug Fixes
---------

- Fix a bug where pyenv cannot be found when PYENV_ROOT is not set  `#29 <https://github.com/sarugaku/pythonfinder/issues/29>`_
  
- Fix a bug where pyenv python location is not properly got by sysconfig._get_default_scheme  `#31 <https://github.com/sarugaku/pythonfinder/issues/31>`_
  
- Fix finding pyenv's python versions issue when pyenv root version is not present  `#33 <https://github.com/sarugaku/pythonfinder/issues/33>`_


1.1.7 (2018-11-04)
==================

Features & Improvements
-----------------------

- Pyenv paths will now be ordered respecting global version settings and pyenv shims will be removed from the search path.  `#27 <https://github.com/sarugaku/pythonfinder/issues/27>`_
  

Bug Fixes
---------

- Fixed an issue with unnesting paths when finding python versions.  `#24 <https://github.com/sarugaku/pythonfinder/issues/24>`_
  
- Fixed a bug with searching windows registry entries which sometimes caused errors for uninstalled python instances.  `#26 <https://github.com/sarugaku/pythonfinder/issues/26>`_


1.1.6 (2018-10-26)
==================

No significant changes.


1.1.5 (2018-10-25)
==================

Bug Fixes
---------

- Fixed an issue with parsing python paths.  `#52 <https://github.com/sarugaku/pythonfinder/issues/52>`_


1.1.4 (2018-10-25)
==================

Bug Fixes
---------

- Fixed a broken call to ``vistir.misc.run`` which returned a ``subprocess.Popen`` object instead of its output.  `#22 <https://github.com/sarugaku/pythonfinder/issues/22>`_


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
