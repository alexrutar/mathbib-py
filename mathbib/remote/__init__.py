from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final, Optional, Callable, Iterable
    from .utils import RelatedRecord

    ParsedRecord = tuple[dict, Iterable[RelatedRecord]]
    RecordParser = Callable[[str], ParsedRecord]
    URLBuilder = Callable[[str], str]
    IdentifierValidator = Callable[[str], bool]

from dataclasses import dataclass
from enum import IntEnum, auto
import tomllib

from xdg_base_dirs import xdg_data_home, xdg_cache_home

from . import doi, zbl, arxiv, zbmath, isbn, ol
from ..term import TermWrite


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
    show_url: Optional[URLBuilder] = None
    download_url: Optional[URLBuilder] = None


_REMOTES: Final = {
    RemoteKey.ZBL: RemoteRecord(
        RemoteKey.ZBL,
        zbl.url_builder,
        zbl.record_parser,
        zbl.validate_identifier,
        show_url=zbl.show_url,
    ),
    RemoteKey.DOI: RemoteRecord(
        RemoteKey.DOI,
        doi.url_builder,
        doi.record_parser,
        doi.validate_identifier,
        show_url=doi.show_url,
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
        show_url=arxiv.show_url,
        download_url=arxiv.download_url,
    ),
    RemoteKey.ISBN: RemoteRecord(
        RemoteKey.ISBN,
        isbn.url_builder,
        isbn.record_parser,
        isbn.validate_identifier,
        show_url=isbn.show_url,
    ),
    RemoteKey.OL: RemoteRecord(
        RemoteKey.OL,
        ol.url_builder,
        ol.record_parser,
        ol.validate_identifier,
        show_url=ol.show_url,
    ),
}


def get_remote_record(keyid: KeyId) -> RemoteRecord:
    return _REMOTES[keyid.key]


class KeyIdError(Exception):
    def __init__(self, message="Invalid KeyId"):
        self.message = message
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
        """Build the KeyId from a string, with validation using the
        internal validation methods."""
        tokens = keyid_str.split(":")
        if len(tokens) >= 2:
            if tokens[0].upper() in RemoteKey.__members__:
                key, identifier = RemoteKey[tokens[0].upper()], ":".join(tokens[1:])
                if _REMOTES[key].validate_identifier(identifier):
                    return cls(key, identifier)
                else:
                    raise KeyIdIdentifierError(key, identifier)
            else:
                raise KeyIdKeyError(tokens[0])
        else:
            raise KeyIdFormatError(keyid_str)

    @classmethod
    def _from_str_no_check(cls, keyid_str: str) -> KeyId:
        tokens = keyid_str.split(":")
        return cls(RemoteKey[tokens[0].upper()], ":".join(tokens[1:]))

    def toml_path(self):
        ret = (
            xdg_data_home()
            / "mathbib"
            / "records"
            / str(self.key)
            / f"{self.identifier}.toml"
        )
        ret.parent.mkdir(parents=True, exist_ok=True)
        return ret

    def file_path(self, suffix: str = "pdf"):
        ret = (
            xdg_data_home()
            / "mathbib"
            / "files"
            / str(self.key)
            / f"{self.identifier}.{suffix}"
        )
        ret.parent.mkdir(parents=True, exist_ok=True)
        return ret

    def cache_path(self):
        ret = (
            xdg_cache_home()
            / "mathbib"
            / "records"
            / str(self.key)
            / f"{self.identifier}.json"
        )
        ret.parent.mkdir(parents=True, exist_ok=True)
        return ret

    def toml_record(self, warn: bool = False):
        try:
            return tomllib.loads(self.toml_path().read_text())
        except FileNotFoundError:
            return {}
        except tomllib.TOMLDecodeError as e:
            if warn:
                TermWrite.warn(f"Invalid TOML in {self}: {e}")
                return {}
            else:
                raise e

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
