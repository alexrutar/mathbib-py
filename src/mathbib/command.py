from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional

from pathlib import Path
from json import dumps

import click

from .bibtex import BibTexHandler
from .citegen import generate_biblatex
from .external import parse_key_id
from .record import ArchiveRecord, resolve_records


@click.group()
@click.version_option(prog_name="mbib (mathbib)")
@click.option("--verbose/--silent", "-v/-V", "verbose", default=True, help="Be verbose")
@click.option("--debug/--no-debug", "debug", default=False, help="Debug mode")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool) -> None:
    """MathBib is a tool to help streamline the management of BibLaTeX files associated
    with records from various mathematical repositories.
    """
    ctx.obj = {
        "verbose": verbose,
        "debug": debug,
    }


@cli.command(short_help="Generate citations from keys in file.")
@click.argument(
    "texfile",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, writable=True, path_type=Path
    ),
    metavar="TEXFILE",
)
@click.option(
    f"--out",
    f"out",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, writable=True, path_type=Path
    ),
    help=f"Output file path.",
)
def generate(texfile: Iterable[Path], out: Optional[Path]):
    """Parse TEXFILE and generate bibtex entries corresponding to keys.
    If option --out is specified, write generated text to file.
    """
    bibstr = generate_biblatex(*texfile)
    if out is None:
        click.echo(bibstr, nl=False)
    else:
        out.write_text(bibstr)


@cli.group(name="get", short_help="Retrieve various records from KEY:ID pairs.")
def get_group():
    pass


@get_group.command(name="json", short_help="Get record from KEY:ID pair")
@click.argument("key_id", type=str, metavar="KEY:ID")
def json_cmd(key_id: str):
    """Generate a JSON record for KEY:ID."""
    key, identifier = parse_key_id(key_id)
    click.echo(dumps(resolve_records(key, identifier)))


@get_group.command(name="bibtex", short_help="Get bibtex from KEY:ID pair")
@click.argument("key_id", type=str, metavar="KEY:ID")
def bibtex(key_id: str):
    """Generate a BibTeX record for KEY:ID."""
    bth = BibTexHandler()
    click.echo(bth.write_records((ArchiveRecord(key_id),)), nl=False)
