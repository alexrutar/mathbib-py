from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Type
    from types import TracebackType
    from pathlib import Path

    from .record import ArchiveRecord

from .bibtex import BibTexHandler
from .request import RemoteSession
from .partition import Partition
from .remote.error import NullRecordError

from tomllib import loads, TOMLDecodeError

import click
from tomli_w import dumps


class CLISession:
    def __init__(
        self,
        debug: bool,
        cache: bool,
        remote: bool,
        relation_file: Path,
        alias_file: Path,
    ):
        self.debug = debug
        self.cache = cache
        self.remote = remote
        self.relation_file = relation_file
        self.alias_file = alias_file

    def add_alias(self, alias: str, record: ArchiveRecord):
        keyid = record.keyid.drop_alias()
        if record.is_null():
            raise NullRecordError(keyid)

        if alias in self.alias.keys():
            raise click.ClickException(
                f"Alias '{alias}' already exists. Delete first to overwrite."
            )

        self.alias[alias] = str(keyid)

    def delete_alias(self, alias: str):
        try:
            del self.alias[alias]
        except KeyError:
            raise click.ClickException(f"No alias with name '{alias}'")

    def get_alias(self, alias: str) -> str:
        try:
            return self.alias[alias]
        except KeyError:
            raise click.ClickException(f"No alias with name '{alias}'")

    def __enter__(self):
        try:
            self.alias: dict[str, str] = loads(self.alias_file.read_text())
        except FileNotFoundError:
            self.alias: dict[str, str] = {}
        except TOMLDecodeError:
            raise click.ClickException(
                f"Corrputed alias file at '{self.alias_file}'."
                "Fix or delete this file to continue."
            )

        self.remote_session = RemoteSession(cache=self.cache, remote=self.remote)

        try:
            self.relations = Partition.from_serialized(self.relation_file.read_text())
        except FileNotFoundError:
            self.relations = Partition()

        self.bibtex_handler = BibTexHandler()

        return self

    # TODO: properly catch errors here!
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        self.alias_file.parent.mkdir(exist_ok=True, parents=True)
        self.alias_file.write_text(dumps(self.alias))

        if self.cache:
            self.relation_file.parent.mkdir(exist_ok=True, parents=True)
            self.relation_file.write_text(self.relations.serialize())
