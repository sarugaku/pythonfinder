import datetime
import os
import pathlib
import re
import shutil
import subprocess
import time
from pathlib import Path

import invoke
import parver
from towncrier._builder import find_fragments, render_fragments, split_fragments
from towncrier._settings import load_config

ROOT = pathlib.Path(__file__).resolve().parent.parent

PACKAGE_NAME = "pythonfinder"

INIT_PY = ROOT.joinpath("src", PACKAGE_NAME, "__init__.py")


@invoke.task()
def test(ctx):
    new_path = os.environ["PATH"].split(os.pathsep)
    if os.path.expanduser("~/.pyenv/shims") in new_path:
        new_path.remove(os.path.expanduser("~/.pyenv/shims"))
    if os.path.expanduser("~/.pyenv/bin") in new_path:
        new_path.remove(os.path.expanduser("~/.pyenv/bin"))
    env = {"PYENV_ROOT": "", "PATH": os.pathsep.join(new_path)}
    ctx.run("pytest -ra tests/", env=env)


@invoke.task()
def typecheck(ctx):
    src_dir = ROOT / "src" / PACKAGE_NAME
    src_dir = src_dir.as_posix()
    config_file = ROOT / "setup.cfg"
    env = {"MYPYPATH": src_dir}
    ctx.run(f"mypy {src_dir} --config-file={config_file}", env=env)


def _get_git_root(ctx):
    return Path(ctx.run("git rev-parse --show-toplevel", hide=True).stdout.strip())


def _get_branch(ctx):
    return ctx.run("git rev-parse --abbrev-ref HEAD", hide=True).stdout.strip()


@invoke.task()
def clean(ctx):
    """Clean previously built package artifacts."""
    dist = ROOT.joinpath("dist")
    build = ROOT.joinpath("build")
    print("[clean] Removing dist and build dirs")
    if dist.exists():
        shutil.rmtree(dist.as_posix())
    if build.exists():
        shutil.rmtree(build.as_posix())


def _read_version():
    out = subprocess.check_output(["git", "tag"], encoding="ascii")
    try:
        version = max(
            parver.Version.parse(v.lstrip("v")).normalize()
            for v in (line.strip() for line in out.split("\n"))
            if v
        )
    except ValueError:
        version = parver.Version.parse("0.0.0")
    return version


def _read_text_version():
    lines = INIT_PY.read_text().splitlines()
    match = next(iter(line for line in lines if line.startswith("__version__")), None)
    if match is not None:
        _, _, version_text = match.partition("=")
        version_text = version_text.strip().strip('"').strip("'")
        version = parver.Version.parse(version_text).normalize()
        return version
    else:
        return _read_version()


def _write_version(v):
    lines = []
    with INIT_PY.open() as f:
        for line in f:
            if line.startswith("__version__ = "):
                line = f"__version__ = {repr(str(v))}\n".replace("'", '"')
            lines.append(line)
    with INIT_PY.open("w", newline="\n") as f:
        f.write("".join(lines))


def _render_log():
    """Totally tap into Towncrier internals to get an in-memory result."""
    config = load_config(ROOT)
    definitions = config["types"]
    fragments, fragment_filenames = find_fragments(
        pathlib.Path(config["directory"]).absolute(),
        config["sections"],
        None,
        definitions,
    )
    rendered = render_fragments(
        pathlib.Path(config["template"]).read_text(encoding="utf-8"),
        config["issue_format"],
        split_fragments(fragments, definitions),
        definitions,
        config["underlines"][1:],
        False,  # Don't add newlines to wrapped text.
    )
    return rendered


REL_TYPES = ("major", "minor", "patch", "post")


def _bump_release(version, type_, log=False):
    if type_ not in REL_TYPES:
        raise ValueError(f"{type_} not in {REL_TYPES}")
    index = REL_TYPES.index(type_)
    current_version = version.base_version()
    if version.is_prerelease and type_ == "patch":
        next_version = current_version
    else:
        next_version = current_version.bump_release(index=index)
    if log:
        print(f"[bump] {version} -> {next_version}")
    print(f"{next_version}")
    return next_version


def _prebump(version, prebump, log=False):
    next_version = version.bump_release(index=prebump).bump_dev()
    if log:
        print(f"[bump] {version} -> {next_version}")
    print(f"{next_version}")
    return next_version


PREBUMP = "patch"


@invoke.task(pre=[clean])
def build(ctx):
    ctx.run("python setup.py sdist bdist_wheel")


@invoke.task()
def get_next_version(ctx, type_="patch", log=False):
    version = _read_version()
    if type_ in ("dev", "pre"):
        idx = REL_TYPES.index("patch")
        new_version = _prebump(version, idx, log=log)
    else:
        new_version = _bump_release(version, type_, log=log)
    return new_version


@invoke.task()
def bump_version(ctx, type_="patch", log=False, dry_run=False):
    new_version = get_next_version(ctx, type_, log=log)
    if not dry_run:
        _write_version(new_version)
    return new_version


@invoke.task()
def generate_news(ctx, yes=False, dry_run=False):
    command = "towncrier"
    if dry_run:
        command = f"{command} --draft"
    elif yes:
        command = f"{command} --yes"
    ctx.run(command)


@invoke.task()
def get_changelog(ctx):
    changelog = _render_log()
    print(changelog)
    return changelog


@invoke.task(optional=["version", "type_"])
def tag_release(ctx, version=None, type_="patch", yes=False, dry_run=False):
    if version is None:
        version = bump_version(ctx, type_, log=not dry_run, dry_run=dry_run)
    else:
        _write_version(version)
    tag_content = get_changelog(ctx)
    generate_news(ctx, yes=yes, dry_run=dry_run)
    git_commit_cmd = f'git commit -am "Release {version}"'
    tag_content = tag_content.replace('"', '\\"')
    git_tag_cmd = f'git tag -a {version} -m "Version {version}\n\n{tag_content}"'
    if dry_run:
        print("Would run commands:")
        print(f"    {git_commit_cmd}")
        print(f"    {git_tag_cmd}")
    else:
        ctx.run(git_commit_cmd)
        ctx.run(git_tag_cmd)


@invoke.task(optional=["version", "type_"])
def release(ctx, version=None, type_="patch", yes=False, dry_run=False):
    if version is None:
        version = bump_version(ctx, type_, log=not dry_run, dry_run=dry_run)
    else:
        _write_version(version)
    current_branch = _get_branch(ctx)
    generate_news(ctx, yes=yes, dry_run=dry_run)
    git_commit_cmd = f'git commit -am "Release {version}"'
    git_tag_cmd = f'git tag -a {version} -m "Version {version}"'
    git_push_cmd = f"git push origin {current_branch}"
    git_push_tags_cmd = "git push --tags"
    if dry_run:
        print("Would run commands:")
        print(f"    {git_commit_cmd}")
        print(f"    {git_tag_cmd}")
        print(f"    {git_push_cmd}")
        print(f"    {git_push_tags_cmd}")
    else:
        ctx.run(git_commit_cmd)
        ctx.run(git_tag_cmd)
        ctx.run(git_push_cmd)
        print("Waiting 5 seconds before pushing tags...")
        time.sleep(5)
        ctx.run(git_push_tags_cmd)


@invoke.task(pre=[clean])
def full_release(ctx, type_, repo, prebump=PREBUMP, yes=False):
    """Make a new release."""
    if prebump not in REL_TYPES:
        raise ValueError(f"{type_} not in {REL_TYPES}")
    prebump = REL_TYPES.index(prebump)

    version = bump_version(ctx, type_, log=True)

    # Needs to happen before Towncrier deletes fragment files.

    tag_release(version, yes=yes)

    ctx.run("python setup.py sdist bdist_wheel")

    dist_pattern = f'{PACKAGE_NAME.replace("-", "[-_]")}-*'
    artifacts = list(ROOT.joinpath("dist").glob(dist_pattern))
    filename_display = "\n".join(f"  {a}" for a in artifacts)
    print(f"[release] Will upload:\n{filename_display}")
    if not yes:
        try:
            input("[release] Release ready. ENTER to upload, CTRL-C to abort: ")
        except KeyboardInterrupt:
            print("\nAborted!")
            return

    arg_display = " ".join(f'"{n}"' for n in artifacts)
    ctx.run(f'twine upload --repository="{repo}" {arg_display}')

    version = _prebump(version, prebump)
    _write_version(version)

    ctx.run(f'git commit -am "Prebump to {version}"')


@invoke.task
def build_docs(ctx):
    _current_version = _read_version()
    minor = [str(i) for i in _current_version.release[:2]]
    docs_folder = (ROOT / "docs").as_posix()
    if not docs_folder.endswith("/"):
        docs_folder = "{0}/".format(docs_folder)
    args = ["--ext-autodoc", "--ext-viewcode", "-o", docs_folder]
    args.extend(["-A", "'Dan Ryan <dan@danryan.co>'"])
    args.extend(["-R", str(_current_version)])
    args.extend(["-V", ".".join(minor)])
    args.extend(["-e", "-M", "-F", f"src/{PACKAGE_NAME}"])
    print("Building docs...")
    ctx.run("sphinx-apidoc {0}".format(" ".join(args)))


@invoke.task
def clean_mdchangelog(ctx):
    changelog = ROOT / "CHANGELOG.md"
    content = changelog.read_text()
    content = re.sub(
        r"([^\n]+)\n?\s+\[\\(#\d+)\]\(https://github\.com/sarugaku/[\w\-]+/issues/\d+\)",
        r"\1 \2",
        content,
        flags=re.MULTILINE,
    )
    changelog.write_text(content)


ns = invoke.Collection(
    typecheck,
    build_docs,
    release,
    clean_mdchangelog,
    build,
    get_next_version,
    bump_version,
    generate_news,
    get_changelog,
    tag_release,
    test,
)
