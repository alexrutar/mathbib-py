from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final, Optional, Callable

    RelatedRecords = dict[
        str, str | tuple[Callable[[str], str], Callable[[str], Optional[str]]]
    ]
    ParsedRecord = tuple[dict, RelatedRecords]
    RecordParser = Callable[[str], ParsedRecord]
    URLBuilder = Callable[[str], str]
    IdentifierValidator = Callable[[str], bool]

from dataclasses import dataclass
from enum import IntEnum, auto
import tomllib

from xdg_base_dirs import xdg_data_home, xdg_cache_home

from . import doi, zbl, arxiv, zbmath, isbn, ol


class RemoteKey(IntEnum):
    """Note: the order of declaration is also used as the priority order
    for various other functionalities.
    """

    ZBL = auto()
    DOI = auto()
    ZBMATH = auto()
    ARXIV = auto()
    ISBN = auto()
    OL = auto()

    def __str__(self):
        return self.name.lower()


@dataclass(frozen=True)
class RemoteRecord:
    key: RemoteKey
    build_url: URLBuilder
    parse_record: RecordParser
    validate_identifier: IdentifierValidator


REMOTES: Final = {
    RemoteKey.ZBL: RemoteRecord(
        RemoteKey.ZBL, zbl.url_builder, zbl.record_parser, zbl.validate_identifier
    ),
    RemoteKey.DOI: RemoteRecord(
        RemoteKey.DOI, doi.url_builder, doi.record_parser, doi.validate_identifier
    ),
    RemoteKey.ZBMATH: RemoteRecord(
        RemoteKey.ZBMATH,
        zbmath.url_builder,
        zbmath.record_parser,
        zbmath.validate_identifier,
    ),
    RemoteKey.ARXIV: RemoteRecord(
        RemoteKey.ARXIV,
        arxiv.url_builder,
        arxiv.record_parser,
        arxiv.validate_identifier,
    ),
    RemoteKey.ISBN: RemoteRecord(
        RemoteKey.ISBN, isbn.url_builder, isbn.record_parser, isbn.validate_identifier
    ),
    RemoteKey.OL: RemoteRecord(
        RemoteKey.OL, ol.url_builder, ol.record_parser, ol.validate_identifier
    ),
}


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
                if REMOTES[key].validate_identifier(identifier):
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

    def toml_record(self):
        try:
            return tomllib.loads(self.toml_path().read_text())
        except FileNotFoundError:
            return {}

    def cache_path(self):
        return xdg_cache_home() / "mathbib" / str(self.key) / f"{self.identifier}.json"

    def __str__(self):
        return f"{self.key}:{self.identifier}"

    def __repr__(self):
        return f"{self.key}:{self.identifier}"


@dataclass(frozen=True)
class AliasedKeyId(KeyId):
    key: RemoteKey
    identifier: str
    alias: Optional[str] = None

    @classmethod
    def from_str(cls, keyid_str: str, alias: Optional[str] = None):
        sub = super().from_str(keyid_str)
        return cls(sub.key, sub.identifier, alias)

    def drop_alias(self) -> KeyId:
        return KeyId(self.key, self.identifier)
