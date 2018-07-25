Added efficient crawling and caching when searching for python and other executables.
- Carry architecture support all the way through the search stack to only return available python which matches the desired architecture.
- Improve sub-path consolidations for searching for executables and pythons.
- Use lazy loading of python versions to avoid unnecessary subprocess calls.
