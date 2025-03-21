Refactor pythonfinder for improved efficiency and PEP 514 support
Summary

This PR completely refactors the pythonfinder module to improve efficiency, reduce logical errors, and fix support for PEP 514 (Python registration in the Windows registry). The refactoring replaces the complex object hierarchy with a more modular, composition-based approach that is easier to maintain and extend.
Motivation

The original pythonfinder implementation had several issues:

    Complex object wrapping with paths as objects, leading to excessive recursion
    Tight coupling between classes making the code difficult to follow and maintain
    Broken Windows registry support (PEP 514)
    Performance issues due to redundant path scanning and inefficient caching

Changes

    Architecture: Replaced inheritance-heavy design with a composition-based approach using specialized finders
    Data Model: Simplified the data model with a clean PythonInfo dataclass
    Windows Support: Implemented proper PEP 514 support for Windows registry
    Performance: Improved caching and reduced redundant operations
    Error Handling: Added more specific exceptions and better error handling

Features

The refactored implementation continues to support all required features:

    System and user PATH searches
    pyenv installations
    asdf installations
    Windows registry (PEP 514) - now working correctly

Implementation Details

The new implementation is organized into three main components:

    Finders: Specialized classes for finding Python in different locations
        SystemFinder: Searches in the system PATH
        PyenvFinder: Searches in pyenv installations
        AsdfFinder: Searches in asdf installations
        WindowsRegistryFinder: Implements PEP 514 for Windows registry

    Models: Simple data classes for storing Python information
        PythonInfo: Stores information about a Python installation

    Utils: Utility functions for path and version handling
        path_utils.py: Path-related utility functions
        version_utils.py: Version-related utility functions
