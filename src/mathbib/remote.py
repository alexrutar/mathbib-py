from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime, timedelta
import json
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

from xdg_base_dirs import xdg_cache_home

from .error import RemoteAccessError, RemoteParseError

if TYPE_CHECKING:
    from typing import Callable


class RemoteRecord:
    CACHE_DATE_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"

    def __init__(
        self,
        key: str,
        url_builder: Callable[[str], str],
        record_parser: Callable[[str], dict],
        error_parser: Callable[[str], dict] | None = None,
    ):
        self.key = key
        self.cache_folder = xdg_cache_home() / "mathbib" / key
        self.url_builder = url_builder
        self.record_parser = record_parser
        self.error_parser = error_parser

    def load_cached_record(self, cache_file: Path) -> dict:
        return json.loads(cache_file.read_text())["record"]

    def get_cache_file(self, identifier: str) -> Path:
        """Get the cache file associated with the item identifier."""
        return self.cache_folder / f"{identifier}.json"

    def load_remote_record(self, identifier: str) -> dict:
        """Load and parse the remote record."""
        url = self.url_builder(identifier)
        try:
            with urlopen(url) as fp:
                return self.record_parser(fp.read().decode("utf8"))
        except (HTTPError, RemoteAccessError) as e:
            raise RemoteAccessError(
                f"Failed to access '{self.key}:{identifier}' from '{url}'"
            ) from e
        except RemoteParseError as e:
            raise RemoteParseError(
                f"While processing '{self.key}:{identifier}': " + e.message
            ) from e

    def update_cached_record(self, identifier: str) -> None:
        """Forcibly update the cache from the remote record."""
        record = self.load_remote_record(identifier)
        self.serialize(identifier, record)

    def update_records(self, max_age: timedelta = timedelta(days=365)):
        """Update all records which are over a certain age."""
        for cache_file in self.cache_folder.glob("*.json"):
            cache_object = json.loads(cache_file.read_text())
            age = datetime.now() - datetime.strptime(
                cache_object["accessed"], self.CACHE_DATE_FORMAT
            )
            if age > max_age:
                self.update_cached_record(cache_file.stem)

    def load_record(self, identifier: str) -> dict:
        """Load the item identifier, defaulting to the cache if possible and
        writing to the cache after loading."""
        cache_file = self.get_cache_file(identifier)

        # attempt to load from cache
        try:
            local_record = self.load_cached_record(cache_file)
        except FileNotFoundError:
            local_record = None

        if local_record is None:
            record = self.load_remote_record(identifier)
            self.serialize(identifier, record)
        else:
            record = local_record

        record[self.key] = identifier
        return record

    def serialize(self, identifier: str, record: dict) -> None:
        self.cache_folder.mkdir(parents=True, exist_ok=True)

        target = self.get_cache_file(identifier)
        cache_object = {
            "record": record,
            "accessed": datetime.now().strftime(self.CACHE_DATE_FORMAT),
        }
        target.write_text(json.dumps(cache_object))
