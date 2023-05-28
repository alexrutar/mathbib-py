from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import KeyId

import click


class RemoteError(click.ClickException):
    def __init__(self, message: str):
        super().__init__(message)
        self.exit_code = 1

    def show(self):
        click.secho("Error: ", fg="red", bold=True, nl=False, err=True)
        click.echo(self.message, err=True)


class RemoteAccessError(RemoteError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RemoteParseError(RemoteError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NullRecordError(RemoteError):
    def __init__(self, keyid: KeyId):
        self.keyid = keyid
        super().__init__(f"KEY:ID '{keyid}' is a null record.")
