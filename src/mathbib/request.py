from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    from pathlib import Path
    from .remote import URLBuilder, KeyId

from datetime import datetime
import json

import click
import requests
import sys
import tomllib

from xdg_base_dirs import xdg_config_home

from . import __version__
from .term import TermWrite
from .remote import get_remote_record


class RemoteSession:
    def __init__(
        self,
        timeout: float = 30,
        info: bool = True,
        cache: bool = True,
        remote: bool = True,
    ):
        self.session = requests.Session()

        contact_email = tomllib.loads(
            (xdg_config_home() / "mathbib" / "config.toml").read_text()
        ).get("email")
        if contact_email is not None:
            self.session.headers.update(
                {"User-Agent": f"MathBib/{__version__} (mailto:{contact_email})"}
            )

        self.timeout = timeout
        self.print_info = info
        self.cache = cache
        self.remote = remote

    def _clear_cache(self, keyid: KeyId):
        keyid.cache_path().unlink(missing_ok=True)

    def _load_cached_record(
        self, keyid: KeyId
    ) -> Optional[tuple[Optional[dict], list[tuple[str, str]]]]:
        """Load the cached record if self.cache: otherwise return a null record"""
        try:
            if self.cache:
                cache = json.loads(keyid.cache_path().read_text())
                return cache["record"], cache["related"]

        # cache is corrupted
        except (KeyError, json.decoder.JSONDecodeError):
            self._clear_cache(keyid)

        except FileNotFoundError:
            pass

        return None

    def _load_remote_record(
        self, keyid: KeyId
    ) -> tuple[Optional[dict], list[tuple[str, str]]]:
        """Load and parse the remote record."""
        remote_record = get_remote_record(keyid)
        response = self.make_request(keyid, remote_record.build_url)
        if response is not None:
            record, related = get_remote_record(keyid).parse_record(response)

            # resolve the related records
            candidates = [rel.resolve(keyid, self) for rel in related]

            return (
                record,
                [(str(keyid.key), keyid.identifier)]
                + [rel for rel in candidates if rel is not None],
            )

        return None, []

    def load_record(self, keyid: KeyId) -> tuple[Optional[dict], list[tuple[str, str]]]:
        """Attempt to load the record associated with keyid and cache a list of
        related records. At this stage, the related records are not "final": they are
        resolved (so they are strings) but otherwise the related records may not actually
        be real records.
        """
        remote_record = get_remote_record(keyid)

        if not remote_record.validate_identifier(keyid.identifier):
            return None, []

        # load cached record
        cache = self._load_cached_record(keyid)

        # if no cache hit, get remote record and cache
        if cache is None:
            record, related = self._load_remote_record(keyid)
            self.serialize(keyid, record, related)
            return record, related

        else:
            return cache

    def serialize(
        self,
        keyid: KeyId,
        record: Optional[dict],
        related: list[tuple[str, str]],
    ) -> None:
        if self.cache:
            target = keyid.cache_path()
            target.parent.mkdir(parents=True, exist_ok=True)
            cache_object = {
                "record": record,
                "accessed": datetime.now().isoformat(),
                "related": related,
            }
            target.write_text(json.dumps(cache_object))

    def make_request(self, keyid: KeyId, build_url: URLBuilder) -> Optional[str]:
        return self.make_raw_request(build_url(keyid.identifier))

    def make_raw_request(self, url: str) -> Optional[str]:
        if self.remote:
            if self.print_info:
                TermWrite.remote(url)
            res = self.session.get(url, timeout=self.timeout)

            if res.status_code == requests.codes.ok:
                return res.text
        return None

    def make_raw_streaming_request(self, url: str, target: Path) -> bool:
        """Attempt to download the file, and return a boolean indicating success."""
        if self.remote:
            TermWrite.download(url)
            res = self.session.get(url, stream=True, timeout=self.timeout)

            # stream the download, and display a progress bar if isatty
            if res.status_code == requests.codes.ok:
                target.parent.mkdir(exist_ok=True, parents=True)
                chunk_size = 8192
                length = res.headers.get("content-length")

                if length is not None and sys.stdout.isatty() and self.print_info:
                    steps = int(int(length) / chunk_size)

                    with target.open("wb") as fd:
                        with click.progressbar(
                            res.iter_content(chunk_size=chunk_size), length=steps
                        ) as bar:
                            for chunk in bar:
                                fd.write(chunk)
                else:
                    with target.open("wb") as fd:
                        for chunk in res.iter_content(chunk_size=chunk_size):
                            fd.write(chunk)
                return True

        return False
