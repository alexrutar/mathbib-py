from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable

from datetime import datetime, timedelta
import json
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

from xdg_base_dirs import xdg_cache_home

from .error import RemoteAccessError, RemoteParseError


class RemoteRecord:
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

    def get_cache_path(self, identifier: str) -> Path:
        """Get the cache file associated with the item identifier."""
        return self.cache_folder / f"{identifier}.json"

    def serialize(self, identifier: str, record: dict) -> None:
        target = self.get_cache_path(identifier)
        target.parent.mkdir(parents=True, exist_ok=True)
        cache_object = {
            "record": record,
            "accessed": datetime.now().isoformat(),
        }
        target.write_text(json.dumps(cache_object))

    def load_cached_record(self, identifier: str) -> dict:
        cache_file = self.get_cache_path(identifier)
        return json.loads(cache_file.read_text())["record"]

    def delete_cached_record(self, identifier: str):
        cache_file = self.get_cache_path(identifier)
        cache_file.unlink(missing_ok=True)

    def update_cached_record(self, identifier: str) -> None:
        """Forcibly update the cache from the remote record."""
        record = self.load_remote_record(identifier)
        self.serialize(identifier, record)

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

    def update_records(self, max_age: timedelta = timedelta(days=365)):
        """Update all cached records which are over a certain age."""
        for cache_file in self.cache_folder.glob("*.json"):
            cache_object = json.loads(cache_file.read_text())
            age = datetime.now() - datetime.fromisoformat(cache_object["accessed"])
            if age > max_age:
                self.update_cached_record(cache_file.stem)

    def load_record(self, identifier: str) -> dict:
        """Load the item identifier, defaulting to the cache if possible and
        writing to the cache after loading."""
        # attempt to load from cache
        try:
            local_record = self.load_cached_record(identifier)
        except FileNotFoundError:
            local_record = None

        if local_record is None:
            record = self.load_remote_record(identifier)
            self.serialize(identifier, record)
        else:
            record = local_record

        record[self.key] = identifier
        return record
