from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional, Sequence

from pathlib import Path
from tomllib import loads, TOMLDecodeError

import click

from .citegen import generate_biblatex, get_citekeys_from_paths
from .record import ArchiveRecord
from .remote import AliasedKeyId, KeyIdError
from .remote.error import RemoteAccessError
from .session import CLISession
from .term import TermWrite

from tomli_w import dumps
from xdg_base_dirs import xdg_data_home
import shutil


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
@click.option(
    "--remote/--no-remote", "remote", default=True, help="Access remote records"
)
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
    If option --out is specified, write generated text to the given file.
    """
    bibstr = generate_biblatex(ctx.obj, *texfile)
    if out is None:
        click.echo(bibstr, nl=False)
    else:
        out.write_text(bibstr)


@cli.group(name="get", short_help="Retrieve records.")
def get_group():
    """Retrieve various record types associated with KEYI:ID records."""


@get_group.command(name="json", short_help="Get record from KEY:ID.")
@record_argument
def json_cmd(record: ArchiveRecord):
    """Generate a JSON record for KEY:ID."""
    click.echo(record.as_json())


@get_group.command(name="bibtex", short_help="Get bibtex from KEY:ID.")
@record_argument
def bibtex(record: ArchiveRecord):
    """Generate a BibTeX record for KEY:ID."""
    # TODO: option to pass multiple records
    click.echo(record.cli_session.bibtex_handler.write_records((record,)), nl=False)


@get_group.command(name="key", short_help="Get highest priority key from KEY:ID.")
@record_argument
def key(record: ArchiveRecord):
    """Generate a BibTeX record for KEY:ID."""
    click.echo(record.priority_key())


@cli.group(name="file", short_help="Access and manage files associated with records.")
def file_group():
    """Access and manage PDF files associated with records."""


@file_group.command(name="open", short_help="Open file associated with KEY:ID.")
@record_argument
def open_cmd(record: ArchiveRecord):
    """Open the PDF file associated with record KEY:ID using the default
    PDF viewer on your device. If the file does not exist, attempt to download
    it from from a standardized location.
    """
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
    raise click.ClickException("Could not find associated file.")


# TODO: turn this into general record listing
@file_group.command(name="list", short_help="List all files.")
@click.pass_obj
def file_list(session: CLISession):
    """List all the files saved on your device, along with the corresponding"""
    root = xdg_data_home() / "mathbib" / "files"
    for pat in (xdg_data_home() / "mathbib" / "files").glob("**/*.pdf"):
        key = pat.relative_to(root).parents[-2]
        val = pat.relative_to(root / key).with_suffix("")
        record = ArchiveRecord.from_str(f"{key}:{val}", session).as_bibtex()
        click.echo(record["ID"], nl=False)
        for src in ("author", "year", "title"):
            if src in record.keys():
                click.echo(" - " + record[src], nl=False)
        click.echo()


# TODO: add --force to overwrite manually
@file_group.command(name="add", short_help="Add new file for record.")
@record_argument
@click.argument(
    "source",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    metavar="PDF",
)
def file_add(record: ArchiveRecord, source: Path):
    """Add new resource PDF for record KEY:ID."""
    if record.is_null():
        raise click.ClickException("Cannot add record to invalid key!")
    else:
        target = record.keyid.file_path()
        if source.suffix != ".pdf":
            raise click.ClickException("cannot add non-PDF record")

        if (
            not target.exists()
            or target.exists()
            and click.confirm("Overwrite existing file?")
        ):
            target.parent.mkdir(exist_ok=True, parents=True)
            shutil.copyfile(source, target)


@cli.command(name="edit", short_help="Edit local record.")
@record_argument
def edit_cmd(record: ArchiveRecord):
    """Edit local the record associated with KEY:ID."""
    toml_record = dumps(record.as_toml())

    while True:
        edited = click.edit(toml_record, extension=".toml")
        if edited is not None:
            try:
                loads(edited)
                record.keyid.toml_path().write_text(edited)
                return

            except TOMLDecodeError as e:
                TermWrite.error(f"invalid TOML: {e}")

            if click.confirm("Edit again?"):
                toml_record = edited
            else:
                return
        else:
            return


@cli.command(name="show", short_help="Open remote record in browser.")
@record_argument
def show_cmd(record: ArchiveRecord):
    """Show remote record associated KEY:ID. This searches for the
    highest priority record and opens it in your browser.
    """
    url = record.show_url()
    if url is not None:
        click.launch(url)
    else:
        raise RemoteAccessError(f"No URL associated with {record.keyid}.")


# TODO: add alias rename command
@cli.group(name="alias", short_help="Manage record aliases.")
def alias():
    """Add, delete, obtain, and list all aliases associated with various
    saved records.
    """


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
@click.argument(
    "key_sources",
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    metavar="KEYSOURCE",
)
@click.pass_obj
def list_alias(session: CLISession, key_sources: Sequence[Path]):
    """Print all defined aliases to the terminal. The aliases are printed
    as valid TOML as a list of ALIAS = KEY:ID entries.

    If any file paths are specified, only generate the alias entries corresponding
    to citation keys in the corresponding files.
    """
    if len(key_sources) > 0:
        alias_dict = {
            k: v
            for k, v in session.alias.items()
            if k in get_citekeys_from_paths(*key_sources)
        }
    else:
        alias_dict = session.alias

    click.echo(dumps(alias_dict), nl=False)
