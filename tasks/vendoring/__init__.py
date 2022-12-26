# Taken from pip also
""""Vendoring script, python 3.5 needed"""
import os
import re
import shutil
from pathlib import Path

import invoke
import requests

TASK_NAME = "update"

FILE_WHITE_LIST = (
    "Makefile",
    "vendor.txt",
    "__init__.py",
    "README.rst",
    "_scandir.cpython-36m-x86_64-linux-gnu.so",
)


MANUAL_LICENSES = {
    "pep514tools": "https://raw.githubusercontent.com/zooba/pep514tools/master/LICENSE"
}


def drop_dir(path):
    shutil.rmtree(str(path))


def remove_all(paths):
    for path in paths:
        if path.is_dir():
            drop_dir(path)
        else:
            path.unlink()


def log(msg):
    print(f"[vendoring.{TASK_NAME}] {msg}")


def _get_vendor_dir(ctx):
    git_root = ctx.run("git rev-parse --show-toplevel", hide=True).stdout
    return Path(git_root.strip()) / "src" / "pythonfinder" / "_vendor"


def clean_vendor(ctx, vendor_dir):
    # Old _vendor cleanup
    remove_all(vendor_dir.glob("*.pyc"))
    log("Cleaning %s" % vendor_dir)
    for item in vendor_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(str(item))
        elif item.name not in FILE_WHITE_LIST:
            item.unlink()
        else:
            log("Skipping %s" % item)


def detect_vendored_libs(vendor_dir):
    retval = []
    for item in vendor_dir.iterdir():
        if item.is_dir():
            retval.append(item.name)
        elif item.name.endswith(".pyi"):
            continue
        elif item.name not in FILE_WHITE_LIST:
            retval.append(item.name[:-3])
    return retval


def rewrite_imports(package_dir, vendored_libs):
    for item in package_dir.iterdir():
        if item.is_dir():
            rewrite_imports(item, vendored_libs)
        elif item.name.endswith(".py"):
            rewrite_file_imports(item, vendored_libs)


def rewrite_file_imports(item, vendored_libs):
    """Rewrite 'import xxx' and 'from xxx import' for vendored_libs"""
    text = item.read_text(encoding="utf-8")
    for lib in vendored_libs:
        text = re.sub(
            r"(\n\s*)import %s(\n\s*)" % lib,
            r"\1from pythonfinder._vendor import %s\2" % lib,
            text,
        )
        text = re.sub(
            r"(\n\s*)from %s" % lib, r"\1from pythonfinder._vendor.%s" % lib, text
        )
    item.write_text(text, encoding="utf-8")


def apply_patch(ctx, patch_file_path):
    log("Applying patch %s" % patch_file_path.name)
    ctx.run("git apply --verbose %s" % patch_file_path)


def vendor(ctx, vendor_dir):
    log("Reinstalling vendored libraries")
    # We use --no-deps because we want to ensure that all of our dependencies
    # are added to vendor.txt, this includes all dependencies recursively up
    # the chain.
    ctx.run(
        "pip install -t {0} -r {0}/vendor.txt --no-deps --no-compile".format(
            str(vendor_dir)
        )
    )
    remove_all(vendor_dir.glob("*.dist-info"))
    remove_all(vendor_dir.glob("*.egg-info"))
    # Detect the vendored packages/modules
    vendored_libs = detect_vendored_libs(vendor_dir)
    log("Detected vendored libraries: %s" % ", ".join(vendored_libs))

    # Global import rewrites
    log("Rewriting all imports related to vendored libs")
    for item in vendor_dir.iterdir():
        if item.is_dir():
            rewrite_imports(item, vendored_libs)
        elif item.name not in FILE_WHITE_LIST:
            rewrite_file_imports(item, vendored_libs)

    # Special cases: apply stored patches
    log("Apply patches")
    patch_dir = Path(__file__).parent / "patches"
    for patch in patch_dir.glob("*.patch"):
        apply_patch(ctx, patch)
    download_licenses(ctx, vendor_dir)


@invoke.task
def download_licenses(ctx, vendor_dir=None):
    log("downloading manual licenses")
    if not vendor_dir:
        vendor_dir = _get_vendor_dir(ctx)
    for license_name in MANUAL_LICENSES:
        url = MANUAL_LICENSES[license_name]
        _, _, name = url.rpartition("/")
        library_dir = vendor_dir / license_name
        r = requests.get(url, allow_redirects=True)
        log(f"Downloading {url}")
        r.raise_for_status()
        if library_dir.exists():
            dest = library_dir / name
        else:
            dest = vendor_dir / f"{license_name}.{name}"
        dest.write_bytes(r.content)


@invoke.task
def rewrite_all_imports(ctx):
    vendor_dir = _get_vendor_dir(ctx)
    log("Using vendor dir: %s" % vendor_dir)
    vendored_libs = detect_vendored_libs(vendor_dir)
    log("Detected vendored libraries: %s" % ", ".join(vendored_libs))
    log("Rewriting all imports related to vendored libs")
    for item in vendor_dir.iterdir():
        if item.is_dir():
            rewrite_imports(item, vendored_libs)
        elif item.name not in FILE_WHITE_LIST:
            rewrite_file_imports(item, vendored_libs)


@invoke.task(name=TASK_NAME)
def main(ctx):
    vendor_dir = _get_vendor_dir(ctx)
    log("Using vendor dir: %s" % vendor_dir)
    clean_vendor(ctx, vendor_dir)
    vendor(ctx, vendor_dir)
    log("Revendoring complete")
