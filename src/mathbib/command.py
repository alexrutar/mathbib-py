from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional

from pathlib import Path
import sys

import click

from .bibtex import BibTexHandler
from .citegen import generate_biblatex
from .record import ArchiveRecord
from .remote import AliasedKeyId, KeyIdError
from .term import TermWrite
from .session import CLISession

from xdg_base_dirs import xdg_data_home


def keyid_callback(ctx, _, keyid_str: str) -> AliasedKeyId:
    """Construct the KeyId argument: first check if the keyid is aliased;
    otherwise, try to obtain it directly.
    """
    try:
        return AliasedKeyId.from_str(ctx.obj.alias[keyid_str], alias=keyid_str)
    except KeyError:
        try:
            return AliasedKeyId.from_str(keyid_str)
        except KeyIdError:
            raise click.BadParameter("Invalid alias or KEY:ID.")


def record_callback(ctx, param, keyid_str: str) -> ArchiveRecord:
    """Construct the KeyId argument: first check if the keyid is aliased;
    otherwise, try to obtain it directly.
    """
    return ArchiveRecord(keyid_callback(ctx, param, keyid_str), ctx.obj)


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


@click.group()
@click.version_option(prog_name="mbib (mathbib)")
@click.option("--cache/--no-cache", "cache", default=True, help="Use local cache")
@click.option("--remote/--no-remote", "remote", default=True, help="Use local cache")
@click.option("--debug/--no-debug", "debug", default=False, help="Debug mode")
@click.option(
    "--alias-file",
    "alias_file",
    default=xdg_data_home() / "mathbib" / "alias.toml",
    help="Alias file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=Path),
)
@click.option(
    "--relation-file",
    "relation_file",
    default=xdg_data_home() / "mathbib" / "relations.json",
    help="Alias file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=Path),
)
@click.pass_context
def cli(
    ctx: click.Context,
    cache: bool,
    remote: bool,
    debug: bool,
    alias_file: Path,
    relation_file: Path,
) -> None:
    """MathBib is a tool to help streamline the management of BibLaTeX files associated
    with records from various mathematical repositories.
    """
    ctx.obj = ctx.with_resource(
        CLISession(debug, cache, remote, relation_file, alias_file)
    )


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
@click.pass_context
def generate(ctx: click.Context, texfile: Iterable[Path], out: Optional[Path]):
    """Parse TEXFILE and generate bibtex entries corresponding to keys.
    If option --out is specified, write generated text to file.
    """
    bibstr = generate_biblatex(ctx.obj, *texfile)
    if out is None:
        click.echo(bibstr, nl=False)
    else:
        out.write_text(bibstr)


# TODO: allow getting multiple KEY:ID
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
    # TODO: rather than hard fail, check if the record is valid with
    # is_null(warn=True) and print missing records.
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
    # First, try to open an existing file
    local_file = record.related_file()
    if local_file is not None:
        click.launch(str(local_file))
        return

    # if there is no file, try to download it
    download_file = record.download_file()
    if download_file is not None:
        click.launch(str(download_file))
        return

    # if there is no file, try to download it
    TermWrite.error("Could not find associated file.")
    sys.exit(1)


@cli.command(name="edit", short_help="Edit local record.")
@keyid_argument
def edit_cmd(keyid: AliasedKeyId):
    """Edit local record for KEY:ID."""
    path = keyid.toml_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    click.edit(filename=str(path))


@cli.command(name="show", short_help="Edit local record.")
@record_argument
def show_cmd(record: ArchiveRecord):
    """Show remote record associated KEY:ID."""
    url = record.show_url()
    if url is not None:
        click.launch(url)


@cli.group(name="alias", short_help="Manage record aliases.")
def alias():
    pass


@alias.command(name="add", short_help="Add new alias.")
@alias_argument
@record_argument
def add_alias(alias_name: str, record: ArchiveRecord):
    """Add ALIAS for record KEY:ID."""
    record.cli_session.add_alias(alias_name, record)


@alias.command(name="delete", short_help="Delete alias.")
@alias_argument
@click.pass_obj
def delete_alias(session: CLISession, alias_name: str):
    """Delete record associated with ALIAS."""
    session.delete_alias(alias_name)


@alias.command(name="get", short_help="Get record associated with alias.")
@alias_argument
@click.pass_obj
def get_alias(session: CLISession, alias_name: str):
    """Get record associated with alias."""
    click.echo(session.get_alias(alias_name))


@alias.command(name="list", short_help="List all defined aliases.")
@click.pass_obj
def list_alias(session: CLISession):
    """Get record associated with alias."""
    for name, value in session.alias.items():
        click.echo(f"{name}: {value}")
