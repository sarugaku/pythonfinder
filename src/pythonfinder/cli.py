import logging

import click

from pythonfinder import __version__
from pythonfinder.finder import Finder

logger = logging.getLogger("pythonfinder")


def set_verbose_output(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(name)s: [%(levelname)s] %(message)s"))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)


@click.command()
@click.option("--find", nargs=1, help="Find a specific python version.")
@click.option("--findall", is_flag=True, default=False, help="Find all python versions.")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Verbose output.",
    callback=set_verbose_output,
    expose_value=False,
)
@click.version_option(
    prog_name=click.style("pyfinder", bold=True),
    version=click.style(__version__, fg="yellow"),
)
@click.pass_context
def cli(ctx, find: str | None = None, findall: bool = False):
    finder = Finder()
    if findall:
        versions = finder.find_all_python_versions()
        if versions:
            click.secho("Found python at the following locations:", fg="green")
            for v in versions:
                click.secho(str(v), fg="yellow")
        else:
            click.secho(
                "ERROR: No valid python versions found! Check your path and try again.",
                fg="red",
                err=True,
            )
            ctx.exit(1)
    elif find:
        click.secho("Searching for python: {0!s}".format(find.strip()), fg="yellow")
        found = finder.find_python_version(find.strip())
        if found:
            click.secho("Found python at the following locations:", fg="green")
            click.secho(str(found), fg="yellow")
        else:
            click.secho("Failed to find matching executable...", fg="yellow")
            ctx.exit(1)
    else:
        click.echo("Please provide a command", color="red")
        ctx.exit(1)


if __name__ == "__main__":
    cli()
