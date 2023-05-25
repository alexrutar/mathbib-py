from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional

from pathlib import Path
import sys

import click
from tomllib import TOMLDecodeError

from .bibtex import BibTexHandler
from .citegen import generate_biblatex
from .record import ArchiveRecord
from .external import KeyId, NullRecordError, KeyIdError
from .alias import add_bib_alias, delete_bib_alias, get_bib_alias, alias_path
from .term import TermWrite


def keyid_callback(_ctx, _param, keyid_str: str) -> KeyId:
    try:
        return KeyId.from_str(keyid_str)
    except KeyIdError as e:
        raise click.BadParameter(str(e))


# TODO: add a '--aliased' option to first look up the alias key and automatically pass
# the keyid corresponding to the priority record
keyid_argument = click.argument(
    "keyid", type=str, metavar="KEY:ID", callback=keyid_callback
)
texfile_argument = click.argument(
    "texfile",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, writable=True, path_type=Path
    ),
    metavar="TEXFILE",
)
alias_argument = click.argument("alias_name", type=str, metavar="ALIAS")


# TODO: add --cache/--no-cache option
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
@texfile_argument
@click.option(
    "--out",
    "out",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, writable=True, path_type=Path
    ),
    help="Output file path.",
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


@cli.group(name="get", short_help="Retrieve records.")
def get_group():
    pass


@get_group.command(name="json", short_help="Get record from KEY:ID.")
@keyid_argument
def json_cmd(keyid: KeyId):
    """Generate a JSON record for KEY:ID."""
    click.echo(ArchiveRecord(keyid).as_json())


@get_group.command(name="bibtex", short_help="Get bibtex from KEY:ID.")
@keyid_argument
def bibtex(keyid: KeyId):
    """Generate a BibTeX record for KEY:ID."""
    bth = BibTexHandler()
    try:
        click.echo(bth.write_records((ArchiveRecord(keyid),)), nl=False)
    except KeyError:
        TermWrite.error("Record missing ENTRYTYPE. Cannot generate BibTex.")


@get_group.command(name="key", short_help="Get highest priority key from KEY:ID.")
@keyid_argument
def key(keyid: KeyId):
    """Generate a BibTeX record for KEY:ID."""
    click.echo(ArchiveRecord(keyid).priority_key())


@cli.group(name="file", short_help="Access and manage files associated with records.")
def file_group():
    pass


@file_group.command(name="open", short_help="Open file associated with KEY:ID.")
@keyid_argument
def open_cmd(keyid: KeyId):
    """Open file associated with record KEY:ID."""
    for keyid in ArchiveRecord(keyid).related_keys():
        if click.launch(str(keyid.file_path())) == 0:
            return

    # TODO: if missing file, try to download arxiv and open it instead
    click.echo("Error: Could not find associated file.", err=True)
    sys.exit(1)


@cli.command(name="edit", short_help="Edit local record.")
@keyid_argument
def edit_cmd(keyid: KeyId):
    """Edit local record for KEY:ID."""
    path = keyid.toml_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    click.edit(filename=str(path))


@cli.group(name="alias", short_help="Manage record aliases.")
def alias():
    # TODO: catch tomllib.TOMLDecodeError
    # TODO: can the sub-commands be run underneath?
    pass


@alias.command(name="add", short_help="Add new alias.")
@alias_argument
@keyid_argument
def add_alias(alias_name: str, keyid: KeyId):
    """Add ALIAS for record KEY:ID."""
    try:
        add_bib_alias(alias_name, keyid)
    except NullRecordError:
        TermWrite.error(f"Null record associated with '{keyid}'.")
        sys.exit(1)
    except TOMLDecodeError:
        TermWrite.error(f"Malformed alias file at '{alias_path()}'.")
        sys.exit(1)


@alias.command(name="delete", short_help="Delete alias.")
@alias_argument
def delete_alias(alias_name: str):
    """Delete record associated with ALIAS."""
    try:
        delete_bib_alias(alias_name)
    except KeyError:
        TermWrite.error(f"No alias with name '{alias_name}'.")
        sys.exit(1)
    except TOMLDecodeError:
        TermWrite.error(f"Malformed alias file at '{alias_path()}'.")
        sys.exit(1)


@alias.command(name="get", short_help="Get record associated with alias.")
@alias_argument
def get_alias(alias_name: str):
    """Get record associated with alias."""
    try:
        click.echo(get_bib_alias(alias_name), nl=False)
    except KeyError:
        TermWrite.error(f"No alias with name '{alias_name}'.")
        sys.exit(1)
    except TOMLDecodeError:
        TermWrite.error(f"Malformed alias file at '{alias_path()}'.")
        sys.exit(1)

# TODO: add alias update to update all alias records so the string is as new as possible
# TODO: also have a program to print all 'non-maximal' alias records

# TODO: add mbib view command to open the record somewhere
# TODO: this requires implementing URLs, etc. for all records
