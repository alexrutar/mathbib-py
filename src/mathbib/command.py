from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional

import click

from pathlib import Path
from json import dumps

from .citegen import generate_biblatex
from .search import zbmath_search_bib
from .external import parse_key_id
from .bibtex import BIBTEX_HANDLER
from .record import ArchiveRecord, resolve_records


@click.group()
@click.version_option(prog_name="mbib (mathbib)")
@click.option(
    "-C",
    "dir",
    default=".",
    show_default=True,
    help="working directory",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, writable=True, path_type=Path
    ),
)
@click.option("--verbose/--silent", "-v/-V", "verbose", default=True, help="Be verbose")
@click.option("--debug/--no-debug", "debug", default=False, help="Debug mode")
@click.pass_context
def cli(ctx: click.Context, dir: Path, verbose: bool, debug: bool) -> None:
    """TexProject is a tool to help streamline the creation and distribution of files
    written in LaTeX.
    """
    ctx.obj = {
        "dir": dir,
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


@cli.command(short_help="Search ZBMath for entries from bibtex file.")
@click.argument(
    "bibfile",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, writable=True, path_type=Path
    ),
    metavar="BIBFILE",
)
def search(bibfile: Path):
    click.echo(dumps(zbmath_search_bib(bibfile)))


@cli.group(name="get")
def get_group():
    pass


@get_group.command(name="json", short_help="Get record from KEY:ID pair")
@click.argument("key_id", type=str, metavar="KEY:ID")
def json_cmd(key_id: str):
    """Generate a JSON record for KEY:ID."""
    key, identifier = parse_key_id(key_id)
    click.echo(dumps(resolve_records(key, identifier)))


@get_group.command(name="bibtex", short_help="Get bibtex from KEY:ID pair")
@click.argument("keyid", type=str, metavar="KEY:ID")
def bibtex(keyid: str):
    """Generate a BibTeX record for KEY:ID."""
    click.echo(BIBTEX_HANDLER.write_dict(ArchiveRecord(keyid).as_bibtex()), nl=False)
