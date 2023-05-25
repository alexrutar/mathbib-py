from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final, Optional

from dataclasses import dataclass

from xdg_base_dirs import xdg_data_home

from . import doi, zbl, arxiv, zbmath, isbn, ol
from ..remote import RemoteRecord, RemoteKey


_REMOTES: Final = {
    RemoteKey.ZBL: RemoteRecord(
        "zbl", zbl.url_builder, zbl.record_parser, zbl.validate_identifier
    ),
    RemoteKey.DOI: RemoteRecord(
        "doi", doi.url_builder, doi.record_parser, doi.validate_identifier
    ),
    RemoteKey.ZBMATH: RemoteRecord(
        "zbmath", zbmath.url_builder, zbmath.record_parser, zbmath.validate_identifier
    ),
    RemoteKey.ARXIV: RemoteRecord(
        "arxiv", arxiv.url_builder, arxiv.record_parser, arxiv.validate_identifier
    ),
    RemoteKey.ISBN: RemoteRecord(
        "isbn", isbn.url_builder, isbn.record_parser, isbn.validate_identifier
    ),
    RemoteKey.OL: RemoteRecord(
        "ol", ol.url_builder, ol.record_parser, ol.validate_identifier
    ),
}


def load_record(keyid: KeyId) -> tuple[Optional[dict], dict[str, str]]:
    return _REMOTES[keyid.key].load_record(keyid.identifier)


class NullRecordError(Exception):
    def __init__(self, keyid: KeyId):
        self.keyid = keyid
        super().__init__("KEY:ID '{keyid}' is a null record.")


class KeyIdError(Exception):
    def __init__(self, message="Invalid KeyId"):
        super().__init__(message)


class KeyIdFormatError(KeyIdError):
    def __init__(self, keyid_str: str):
        super().__init__(f"Format for '{keyid_str}' is invalid.")


class KeyIdKeyError(KeyIdError):
    def __init__(self, key: str):
        super().__init__(f"Key '{key}' is invalid.")


class KeyIdIdentifierError(KeyIdError):
    def __init__(self, key: RemoteKey, identifier: str):
        super().__init__(f"Identifier '{identifier}' is invalid for key '{key}'.")


@dataclass(order=True, frozen=True)
class KeyId:
    key: RemoteKey
    identifier: str

    @classmethod
    def from_str(cls, keyid_str: str) -> KeyId:
        """Build the KeyId from a string, with validation using the internal validation methods."""
        tokens = keyid_str.split(":")
        if len(tokens) >= 2:
            if tokens[0].upper() in RemoteKey.__members__:
                key, identifier = RemoteKey[tokens[0].upper()], ":".join(tokens[1:])
                if _REMOTES[key].is_valid_identifier(identifier):
                    return cls(key, identifier)
                else:
                    raise KeyIdIdentifierError(key, identifier)
            else:
                raise KeyIdKeyError(tokens[0])
        else:
            raise KeyIdFormatError(keyid_str)

    def toml_path(self):
        return (
            xdg_data_home()
            / "mathbib"
            / "records"
            / str(self.key)
            / f"{self.identifier}.toml"
        )

    def file_path(self, suffix: str = "pdf"):
        return (
            xdg_data_home()
            / "mathbib"
            / "files"
            / str(self.key)
            / f"{self.identifier}.{suffix}"
        )

    def __str__(self):
        return f"{self.key}:{self.identifier}"

    def __repr__(self):
        return f"{self.key}:{self.identifier}"
