from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional, Sequence, Literal

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
import json
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


def record_callback_multiple(
    ctx, param, keyid_strs: tuple[str]
) -> Iterable[ArchiveRecord]:
    """Construct the KeyId argument: first check if the keyid is aliased;
    otherwise, try to obtain it directly.
    """
    return (
        ArchiveRecord(keyid_callback(ctx, param, keyid_str), ctx.obj)
        for keyid_str in sorted(set(keyid_strs))
    )


keyid_argument = click.argument(
    "keyid", type=str, metavar="KEY:ID", callback=keyid_callback
)
record_argument = click.argument(
    "record", type=str, metavar="KEY:ID", callback=record_callback
)
record_argument_multiple = click.argument(
    "records",
    type=str,
    nargs=-1,
    metavar="[KEY:ID]...",
    callback=record_callback_multiple,
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
    "--alias",
    "-a",
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
    type=click.Path(file_okay=True, dir_okay=False, writable=True, path_type=Path),
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


@cli.command(name="get", short_help="Get record from KEY:ID.")
@click.option(
    "--record-type",
    "-r",
    "record_type",
    type=click.Choice(["bibtex", "json"], case_sensitive=False),
    default="bibtex",
    help="Record type.",
)
@record_argument_multiple
@click.pass_obj
def get(
    session: CLISession,
    record_type: Literal["bibtex", "json"],
    records: Iterable[ArchiveRecord],
):
    """Generate a record for multiple KEY:ID records. Specify the output type
    using -r.

    Input KEY:ID pairs are automatically sorted and duplicates are removed.

    - BibTex records are returned as the string contents of a valid .bib file.
    - JSON records are returned as list of dictionaries containing the associated
    record objects.
    """
    # TODO: option to pass multiple records
    match record_type:
        case "json":
            click.echo(json.dumps([record.as_json_dict() for record in records]))
        case "bibtex":
            click.echo(session.bibtex_handler.write_records(records), nl=False)


@cli.command(name="key", short_help="Get highest priority key from KEY:ID.")
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


@cli.command(name="list", short_help="List all records.")
@click.option(
    "--sep",
    "sep",
    type=str,
    default=" - ",
    help="Separator for titles.",
)
@click.pass_obj
def list_cmd(session: CLISession, sep: str):
    """List all records. The records are printed in the format"""
    for keyid in session.relations.iter_canonical():
        record = ArchiveRecord(
            AliasedKeyId(keyid.key, keyid.identifier), session
        ).as_bibtex()
        click.echo(
            sep.join(
                str(elem)
                for elem in (
                    keyid,
                    record.get("author"),
                    record.get("year"),
                    record.get("title"),
                )
            )
        )
