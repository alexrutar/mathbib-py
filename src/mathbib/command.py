from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional

import click
from click import Context

from pathlib import Path
from json import dumps


from .index import list_records
from .citegen import generate_biblatex
from .search import zbmath_search_bib
from .external import REMOTES, parse_key_id
from .record import resolve_records


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
def cli(ctx: Context, dir: Path, verbose: bool, debug: bool) -> None:
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


@cli.command(name="get-record", short_help="Get record from key:id pair")
@click.argument("key_id", type=str, metavar="KEYID")
def get_record(key_id: str):
    key, identifier = parse_key_id(key_id)
    click.echo(dumps(REMOTES[key].load_record(identifier)))


@cli.command(name="get-all-records", short_help="Get record from key:id pair")
@click.argument("keyid", type=str, metavar="KEYID")
def get_all_records(keyid: str):
    click.echo(dumps(resolve_records(keyid)))


@cli.command(short_help="List all records", name="list")
def list_cmd():
    for record in list_records():
        click.echo(record)
