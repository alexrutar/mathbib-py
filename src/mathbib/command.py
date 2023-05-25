from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional

from pathlib import Path
import sys

import click
from requests.exceptions import ConnectionError

from .bibtex import BibTexHandler
from .citegen import generate_biblatex
from .record import ArchiveRecord
from .remote import AliasedKeyId, KeyIdError
from .alias import (
    add_bib_alias,
    delete_bib_alias,
    get_bib_alias,
    load_alias_dict,
)
from .term import TermWrite


def keyid_callback(ctx, _, keyid_str: str) -> AliasedKeyId:
    """Construct the KeyId argument: first check if the keyid is aliased; otherwise, try to
    obtain it directly.
    """
    try:
        return AliasedKeyId.from_str(ctx.obj["alias"][keyid_str], alias=keyid_str)
    except KeyError:
        try:
            return AliasedKeyId.from_str(keyid_str)
        except KeyIdError:
            raise click.BadParameter("Invalid alias or KEY:ID.")


def record_callback(ctx, param, keyid_str: str) -> ArchiveRecord:
    """Construct the KeyId argument: first check if the keyid is aliased; otherwise, try to
    obtain it directly.
    """
    try:
        record = ArchiveRecord(keyid_callback(ctx, param, keyid_str))
    except ConnectionError:
        # TODO: fail more gracefully
        TermWrite.error(f"Failed to resolve remote server address.")
        sys.exit(1)

    if record.is_null():
        raise click.BadParameter("Null record")
    else:
        return record


keyid_argument = click.argument(
    "keyid", type=str, metavar="KEY:ID", callback=keyid_callback
)
record_argument = click.argument(
    "record", type=str, metavar="KEY:ID", callback=record_callback
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
    ctx.obj = {"verbose": verbose, "debug": debug, "alias": load_alias_dict()}


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
@record_argument
def json_cmd(record: ArchiveRecord):
    """Generate a JSON record for KEY:ID."""
    click.echo(record.as_json())


@get_group.command(name="bibtex", short_help="Get bibtex from KEY:ID.")
@record_argument
def bibtex(record: ArchiveRecord):
    """Generate a BibTeX record for KEY:ID."""
    bth = BibTexHandler()
    try:
        click.echo(bth.write_records((record,)), nl=False)
    except KeyError:
        TermWrite.error("Record missing ENTRYTYPE. Cannot generate BibTex.")


@get_group.command(name="key", short_help="Get highest priority key from KEY:ID.")
@record_argument
def key(record: ArchiveRecord):
    """Generate a BibTeX record for KEY:ID."""
    click.echo(record.priority_key())


@cli.group(name="file", short_help="Access and manage files associated with records.")
def file_group():
    pass


@file_group.command(name="open", short_help="Open file associated with KEY:ID.")
@record_argument
def open_cmd(record: ArchiveRecord):
    """Open file associated with record KEY:ID."""
    for keyid_rel in record.related_keys():
        if click.launch(str(keyid_rel.file_path())) == 0:
            return

    # TODO: if missing file, try to download arxiv and open it instead
    click.echo("Error: Could not find associated file.", err=True)
    sys.exit(1)


@cli.command(name="edit", short_help="Edit local record.")
@keyid_argument
def edit_cmd(keyid: AliasedKeyId):
    """Edit local record for KEY:ID."""
    path = keyid.toml_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    click.edit(filename=str(path))


@cli.group(name="alias", short_help="Manage record aliases.")
def alias():
    pass


@alias.command(name="add", short_help="Add new alias.")
@alias_argument
@keyid_argument
def add_alias(alias_name: str, keyid: AliasedKeyId):
    """Add ALIAS for record KEY:ID."""
    add_bib_alias(alias_name, keyid)


@alias.command(name="delete", short_help="Delete alias.")
@alias_argument
def delete_alias(alias_name: str):
    """Delete record associated with ALIAS."""
    delete_bib_alias(alias_name)


@alias.command(name="get", short_help="Get record associated with alias.")
@alias_argument
def get_alias(alias_name: str):
    """Get record associated with alias."""
    click.echo(get_bib_alias(alias_name))
