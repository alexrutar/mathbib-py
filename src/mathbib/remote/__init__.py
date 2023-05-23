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

from datetime import datetime, timedelta
from enum import IntEnum, auto
import json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from xdg_base_dirs import xdg_cache_home

from .. import __version__


class RemoteKey(IntEnum):
    """Note: the order of declaration is also used as the priority order
    for various other functionalities.
    """

    ZBL = auto()
    DOI = auto()
    ZBMATH = auto()
    ARXIV = auto()

    def __str__(self):
        return self.name.lower()


class RemoteAccessError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RemoteParseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def make_request(identifier: str, url_builder: URLBuilder) -> str:
    url = url_builder(identifier)
    req = Request(url)
    req.add_header(
        "User-Agent", f"MathBib/{__version__} (mailto:api-contact@rutar.org)"
    )

    try:
        with urlopen(req) as fp:
            return fp.read().decode("utf8")
            # record, related = self.record_parser(fp.read().decode("utf8"))
            # return (record, self.resolve_related(identifier, related))

    except (HTTPError, RemoteAccessError) as e:
        raise RemoteAccessError(f"Failed to access '{identifier}' from '{url}'") from e
    except RemoteParseError as e:
        raise RemoteParseError(f"While processing '{identifier}': " + e.message) from e


class RemoteRecord:
    def __init__(
        self,
        key: str,
        url_builder: URLBuilder,
        record_parser: RecordParser,
    ):
        self.key = key
        self.cache_folder = xdg_cache_home() / "mathbib" / key
        self.url_builder = url_builder
        self.record_parser = record_parser

    def get_cache_path(self, identifier: str) -> Path:
        """Get the cache file associated with the item identifier."""
        return self.cache_folder / f"{identifier}.json"

    def serialize(self, identifier: str, record: dict, related: dict[str, str]) -> None:
        target = self.get_cache_path(identifier)
        target.parent.mkdir(parents=True, exist_ok=True)
        cache_object = {
            "record": record,
            "accessed": datetime.now().isoformat(),
            "related": related,
        }
        target.write_text(json.dumps(cache_object))

    def load_cached_record(self, identifier: str) -> tuple[dict, dict[str, str]]:
        cache = json.loads(self.get_cache_path(identifier).read_text())
        return cache["record"], cache["related"]

    def delete_cached_record(self, identifier: str):
        cache_file = self.get_cache_path(identifier)
        cache_file.unlink(missing_ok=True)

    def update_cached_record(self, identifier: str) -> None:
        """Forcibly update the cache from the remote record."""
        record, related = self.load_remote_record(identifier)
        self.serialize(identifier, record, related)

    def resolve_related(
        self, identifier: str, related: RelatedRecords
    ) -> dict[str, str]:
        related_identifiers = {self.key: identifier}

        for key, res in related.items():
            if isinstance(res, str):
                related_identifiers[key] = res
            else:
                url_builder, parser = res
                parsed = parser(make_request(identifier, url_builder))
                if parsed is not None:
                    related_identifiers[key] = parsed

        return related_identifiers

    def load_remote_record(self, identifier: str) -> tuple[dict, dict[str, str]]:
        """Load and parse the remote record."""
        record, related = self.record_parser(make_request(identifier, self.url_builder))
        return (record, self.resolve_related(identifier, related))

    def update_records(self, max_age: timedelta = timedelta(days=365)):
        """Update all cached records which are over a certain age."""
        for cache_file in self.cache_folder.glob("*.json"):
            cache_object = json.loads(cache_file.read_text())
            age = datetime.now() - datetime.fromisoformat(cache_object["accessed"])
            if age > max_age:
                self.update_cached_record(cache_file.stem)

    def load_record(self, identifier: str) -> tuple[dict, dict[str, str]]:
        """Load the item identifier, defaulting to the cache if possible and
        writing to the cache after loading."""
        # attempt to load from cache
        try:
            cache = self.load_cached_record(identifier)
        except FileNotFoundError:
            cache = None

        if cache is None:
            record, related = self.load_remote_record(identifier)
            self.serialize(identifier, record, related)
        else:
            record, related = cache

        return (record, related)
