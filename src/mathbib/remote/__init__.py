from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable, Optional

    RelatedRecords = dict[
        str, str | tuple[Callable[[str], str], Callable[[str], Optional[str]]]
    ]
    ParsedRecord = tuple[dict, RelatedRecords]
    RecordParser = Callable[[str], ParsedRecord]
    URLBuilder = Callable[[str], str]

from datetime import datetime
from enum import IntEnum, auto
import json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from xdg_base_dirs import xdg_cache_home

from .. import __version__
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


class RemoteError(Exception):
    def __init__(self, message: str, identifier: str):
        self.message = message
        self.identifier = identifier
        super().__init__(message)


class RemoteAccessError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RemoteParseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def make_request(identifier: str, build_url: URLBuilder) -> Optional[str]:
    url = build_url(identifier)

    TermWrite.remote(url)

    req = Request(url)
    req.add_header(
        "User-Agent", f"MathBib/{__version__} (mailto:api-contact@rutar.org)"
    )

    try:
        with urlopen(req) as fp:
            return fp.read().decode("utf8")
            # record, related = self.parse_record(fp.read().decode("utf8"))
            # return (record, self.resolve_related(identifier, related))

    except (HTTPError, RemoteAccessError, RemoteParseError):
        return


class RemoteRecord:
    def __init__(
        self,
        key: str,
        url_builder: URLBuilder,
        record_parser: RecordParser,
        identifier_validator: Callable[[str], bool],
    ):
        self.key = key
        self.cache_folder = xdg_cache_home() / "mathbib" / key
        self.build_url = url_builder
        self.parse_record = record_parser
        self.is_valid_identifier = identifier_validator

    def get_cache_path(self, identifier: str) -> Path:
        """Get the cache file associated with the item identifier."""
        return self.cache_folder / f"{identifier}.json"

    def serialize(
        self, identifier: str, record: Optional[dict], related: Optional[dict[str, str]]
    ) -> None:
        target = self.get_cache_path(identifier)
        target.parent.mkdir(parents=True, exist_ok=True)
        cache_object = {
            "record": record,
            "accessed": datetime.now().isoformat(),
            "related": related,
        }
        target.write_text(json.dumps(cache_object))

    def _load_cached_record(
        self, identifier: str
    ) -> tuple[Optional[dict], dict[str, str]]:
        cache = json.loads(self.get_cache_path(identifier).read_text())
        return cache["record"], cache["related"]

    def delete_cached_record(self, identifier: str):
        cache_file = self.get_cache_path(identifier)
        cache_file.unlink(missing_ok=True)

    def resolve_related(
        self, identifier: str, related: RelatedRecords
    ) -> dict[str, str]:
        related_identifiers = {self.key: identifier}

        for key, res in related.items():
            if isinstance(res, str):
                related_identifiers[key] = res
            else:
                url_builder, parser = res
                response = make_request(identifier, url_builder)
                if response is not None:
                    parsed = parser(response)
                    if parsed is not None:
                        related_identifiers[key] = parsed

        return related_identifiers

    def _load_remote_record(
        self, identifier: str
    ) -> tuple[Optional[dict], dict[str, str]]:
        """Load and parse the remote record."""
        response = make_request(identifier, self.build_url)
        if response is not None:
            record, related = self.parse_record(response)
            return (record, self.resolve_related(identifier, related))
        else:
            return None, {}

    def load_record(self, identifier: str) -> tuple[Optional[dict], dict[str, str]]:
        """Load the item identifier, defaulting to the cache if possible and
        writing to the cache after loading.

        If the identifier is invalid, return a null record.
        """
        try:
            cache = self._load_cached_record(identifier)
        except FileNotFoundError:
            cache = None

        if cache is None:
            record, related = self._load_remote_record(identifier)
            self.serialize(identifier, record, related)
            return record, related

        else:
            record, related = cache

        return (record, related)
